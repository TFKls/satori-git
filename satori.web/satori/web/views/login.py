# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import AlertList,StatusBar
from satori.web.utils import xmlparams
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django import forms

class LoginForm(forms.Form):
    login = forms.CharField(label="Login",required=True)
    password = forms.CharField(widget=forms.PasswordInput, label="Password",required=True)

@general_view
def view(request, page_info):
    alerts = AlertList()
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
                alerts.add('Login failed!','danger')
                form = LoginForm()
                return render_to_response('login.html', {'page_info' : page_info, 'form' : form, 'alerts' : alerts })
    else:
        form = LoginForm()
    status = request.GET.get('status',None)
    if status=='regok':
        alerts.add('Registration successful, activation link has been sent.','success')
    if status=='activated':
        alerts.add('Account activated. You may now login.','success')
    if status=='actfailed':
        alerts.add('Activation failed!','danger')
    return render_to_response('login.html', {'page_info' : page_info, 'form' : form, 'alerts' : alerts })


