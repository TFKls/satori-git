# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import AlertList
from satori.web.utils import xmlparams
from django.forms.util import ErrorList
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django import forms


@general_view
def view(request, page_info, id = None):

    if id==None:
        user = page_info.user
    else:
        user = User(int(id))

    user_admin = page_info.is_admin
    change_allowed = user_admin or not user.confirmed
    class ProfileForm(forms.Form):
        if change_allowed:
            firstname = forms.CharField(label="First name",required=False,initial=user.firstname)
            lastname = forms.CharField(label="Last name",required=True,initial=user.lastname)
        else:
            firstname = forms.CharField(label="First name",required=False,widget=forms.TextInput(attrs={'readonly':'readonly'}),initial=user.firstname)
            lastname = forms.CharField(label="Last name",required=True,widget=forms.TextInput(attrs={'readonly':'readonly'}),initial=user.lastname,help_text='This is a confirmed account - identity is locked.')
        oldpass = forms.CharField(label="Old password",required=False,widget=forms.PasswordInput)
        newpass = forms.CharField(label="New password",required=False,widget=forms.PasswordInput)
        confirm = forms.CharField(label="Confirm password",required=False,widget=forms.PasswordInput)
        affiliation = forms.CharField(label="Affiliation",required=False,initial=user.affiliation)
        if user_admin:
            lock_user = forms.BooleanField(label="Confirm identity",required=False)
        
#    parser = xmlparams.parser_from_xml(Global.get_instance().profile_fields,'profile','input')
    form = ProfileForm()
#    form = ProfileForm(data={'firstname' : user.firstname, 'lastname' : user.lastname,'lock_user' : user.confirmed,'affiliation' : user.affiliation})
#    profile_form = xmlparams.ParamsForm(parser=parser,initial=parser.read_oa_map(user.profile_get_map(),check_required=False))
    if request.method!="POST":
        return render_to_response('profile.html', {'page_info' : page_info, 'form' : form})
    alerts = AlertList()
    if request.method=="POST":
#    if 'update' in request.POST.keys():
        form = ProfileForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                if data['newpass']:
                    if data['newpass']!=data['confirm']:
                        alerts.add('Passwords do not match!','danger')
                    else:
                        if user_admin:
                            user.set_password(data['newpass'])
                        else:
                            user.change_password(data['oldpass'],data['newpass'])
                        alerts.add('Password changed.','success')
                if user.firstname!=data['firstname'] or user.lastname!=data['lastname']:
                    user.modify(UserStruct(firstname=data['firstname'],lastname=data['lastname']))
                    alerts.add('Personal data changed.','info')
                if user.affiliation!=data['affiliation']:
                    user.modify(UserStruct(affiliation=data['affiliation']))
                    alerts.add('Affiliation changed.','info')
                if user_admin and data['lock_user'] and not user.confirmed:
                    user.modify(UserStruct(confirmed=True))
                    alerts.add('User identity locked.','info');
                if user_admin and not data['lock_user'] and user.confirmed:
                    user.modify(UserStruct(confirmed=False))
                    alerts.add('User identity unlocked.','info');
                
            except LoginFailed:
                alerts.add('Login unsucessful for password changing!','danger')
                form._errors['oldpass'] = ErrorList();
                form._errors['oldpass'].append('Enter correct data here');
                form._errors['newpass'] = ErrorList();
                form._errors['newpass'].append('Enter correct data here');
                form._errors['confirm'] = ErrorList();
                form._errors['confirm'].append('Enter correct data here');
            except InvalidPassword:
                alerts.add('Invalid password!','danger')
                form._errors['newpass'] = ErrorList();
                form._errors['newpass'].append('Enter correct data here');
                form._errors['confirm'] = ErrorList();
                form._errors['confirm'].append('Enter correct data here');
            except:
                alerts.add('Error updating profile!','danger')
            return render_to_response('profile.html', {'page_info' : page_info, 'form' : form, 'alerts' : alerts}) 
#    if 'update' in request.POST.keys():
#        profile_form = xmlparams.ParamsForm(parser=parser, data=request.POST)
#        if profile_form.is_valid():
#            om = params.dict_to_oa_map(profile_form.cleaned_data)
#            user.profile_set_map(parser.write_oa_map(profile_form.cleaned_data))
#            return render_to_response('changepass.html', {'page_info' : page_info, 'form' : form, 'profile_form' : profile_form})
    return render_to_response('profile.html', {'page_info' : page_info, 'alerts' : alerts, 'form' : form}) 
