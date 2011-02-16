# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django import forms

class RegisterForm(forms.Form):
    login = forms.CharField(required=True,min_length=5,max_length=23,label="Login")
    firstname = forms.CharField(required=True,label="First name")
    lastname = forms.CharField(required=True,label="Last name")
    email = forms.EmailField(required=True,label="E-mail")
    password = forms.CharField(required=True,min_length=5,widget=forms.PasswordInput,label="Password")
    confirm = forms.CharField(required=True,min_length=5,widget=forms.PasswordInput,label="Confirm")
    
    def clean(self):
        data = self.cleaned_data
        password = data.get("password")
        confirm = data.get("confirm")
        if password and confirm and password != confirm:
            self._errors["confirm"] = self.error_class(["Passwords do not match!"])
            del data["password"]
            del data["confirm"]
        return data
        
@general_view
def view(request, page_info):
    if request.method=="POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            profile = OaMap()
            User.register(UserStruct(login=data["login"],firstname=data["firstname"],lastname=data["lastname"],email=data["email"]),password=data["password"],profile=profile.get_map())
            return HttpResponseRedirect(reverse('login'))
    else:
        form = RegisterForm()
    return render_to_response('register.html',{'form' : form})
