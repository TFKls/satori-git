# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response
from django import forms

class UpdateForm(forms.Form):
    password         = forms.CharField(required=True, widget=forms.PasswordInput, label="Old Password")
    new_password     = forms.CharField(required=True, min_length=5, widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(required=True, min_length=5, widget=forms.PasswordInput, label="Confirm Password")

    def clean(self):
        data = self.cleaned_data
        password = data.get("password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            del data["password"]
            raise forms.ValidationError('Passwords do not match!')
        return data

    def delete_passwords(self):
        for arg in ["password", "new_password", "confirm_password"]:
            del data[arg]

@general_view
def view(request, page_info):
    if request.method=="POST":
        form = UpdateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                page_info.user.change_password(
                        old_password=data["password"],
                        new_password=data["new_password"])
                return HttpResponseRedirect(reverse('profile'))
            except LoginFailed:
                form.errors['loginfailed'] = 'Invalid old password!'
            except InvalidPassword as invalid_password:
                form.errors['invalidpassword'] = 'Invalid new password!' 
            except:
                form.errors['loginfailed'] = 'Internal error - try again!'
            form.delete_passwords()
    else:
        form = UpdateForm()
    return render_to_response('profile.html', {'page_info' : page_info,
                                               'form' : form })
