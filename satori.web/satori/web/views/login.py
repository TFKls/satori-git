# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import StatusBar
from satori.web.utils import xmlparams
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django import forms

class LoginForm(forms.Form):
    login = forms.CharField(label="Login:")
    password = forms.CharField(widget=forms.PasswordInput, label="Password:")

@general_view
def view(request, page_info):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login = form.cleaned_data['login']
            password = form.cleaned_data['password']
            try:
                token = User.authenticate(login=login,password=password)
                token_container.set_token(token)
                redir = request.GET.get('redir',None)
                if redir and redir[:8]!='/logout' and redir[:8]!='/login':
                    return HttpResponseRedirect(redir)
                else:
                    return HttpResponseRedirect(reverse('news'))
            except:
                form.errors['__all__']= 'Login failed!'
                return render_to_response('login.html', {'page_info' : page_info, 'form' : form, 'failed' : True })
    else:
        form = LoginForm()
    status = request.GET.get('status',None)
    if status:
        bar = StatusBar()
    else:
        bar = None
    if status=='regok':
        bar.messages.append('Registration successful, activation link has been sent.')
    if status=='activated':
        bar.messages.append('Account activated. You may now login.')
    if status=='actfailed':
        bar.errors.append('Activation failed!')
    return render_to_response('login.html', {'page_info' : page_info, 'form' : form, 'status_bar' : bar })


class ChangePassForm(forms.Form):
    firstname = forms.CharField(label="First name:",required=False)
    lastname = forms.CharField(label="Last name:",required=False)
    oldpass = forms.CharField(label="Old password:",required=False,widget=forms.PasswordInput)
    newpass = forms.CharField(label="New password:",required=False,widget=forms.PasswordInput)
    confirm = forms.CharField(label="Confirm password:",required=False,widget=forms.PasswordInput)
    def clean(self):
        data = self.cleaned_data
        if data["newpass"]!=data["confirm"]:
            raise forms.ValidationError('Passwords do not match!')
            del data["newpass"]
            del data["confirm"]
        return data

@general_view
def profile(request, page_info, id = None):
    if id==None:
        user = page_info.user
    else:
        user = User(int(id))
    a = Global.get_instance().profile_fields
    parser = xmlparams.parser_from_xml(Global.get_instance().profile_fields,'profile','input')
    form = ChangePassForm(data={'firstname' : user.firstname, 'lastname' : user.lastname})
    profile_form = xmlparams.ParamsForm(parser=parser,initial=parser.read_oa_map(user.profile_get_map(),check_required=False))
    if request.method!="POST":
        return render_to_response('changepass.html', {'page_info' : page_info, 'password_form' : form, 'profile_form' : profile_form})
    bar = StatusBar()
    if 'changepass' in request.POST.keys():
        form = ChangePassForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                if id != None and data['newpass']:
                    if data['newpass']==data['confirm']:
                        user.set_password(data['newpass'])
                        bar.messages.append('Password changed.')
                    else:
                        bar.errors.append('Passwords do not match!')
                if data['oldpass']:
                    user.change_password(data['oldpass'],data['newpass'])
                    bar.messages.append('Password changed.')
                if user.firstname!=data['firstname'] or user.lastname!=data['lastname']:
                    user.modify(UserStruct(firstname=data['firstname'],lastname=data['lastname']))
                    bar.messages.append('Personal data changed.')
            except LoginFailed:
                bar.errors.append('Login failed!')
            except InvalidPassword:
                bar.errors.append('Invalid pasword!')
            return render_to_response('changepass.html', {'page_info' : page_info, 'password_form' : form, 'profile_form' : profile_form,'status_bar' : bar}) 
    if 'update' in request.POST.keys():
        profile_form = xmlparams.ParamsForm(parser=parser, data=request.POST)
        if profile_form.is_valid():
#            om = params.dict_to_oa_map(profile_form.cleaned_data)
            user.profile_set_map(parser.write_oa_map(profile_form.cleaned_data))
            return render_to_response('changepass.html', {'page_info' : page_info, 'password_form' : form, 'profile_form' : profile_form})
    return render_to_response('changepass.html', {'page_info' : page_info, 'status_bar' : bar, 'password_form' : form, 'profile_form' : profile_form}) 
