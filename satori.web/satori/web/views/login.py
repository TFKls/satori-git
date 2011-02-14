# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response
from django import forms

class LoginForm(forms.Form):
    login = forms.CharField(label="Login:")
    password = forms.CharField(widget=forms.PasswordInput, label="Password:")

@general_view
def view(request, general_page_overview):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login = form.cleaned_data['login']
            password = form.cleaned_data['password']
            try:
                token = User.authenticate(login=login,password=password)
                token_container.set_token(token)
                return render_to_response('news.html', {'general_page_overview' : general_page_overview})
            except:
                return render_to_response('login.html', {'general_page_overview' : general_page_overview, 'form' : form, 'failed' : True })
    else:
        form = LoginForm()
    return render_to_response('login.html', {'general_page_overview' : general_page_overview, 'form' : form })
