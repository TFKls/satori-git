# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import StatusBar
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
