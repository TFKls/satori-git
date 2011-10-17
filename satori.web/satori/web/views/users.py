# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import StatusBar
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

class EditUserForm(forms.Form):
    login = forms.CharField(required=True,label='User login:')

@general_view
def view(request, page_info):
    if request.method=='POST':
        form = EditUserForm(request.POST)
        bar = StatusBar()
        if form.is_valid():
            try:
                user = User.filter(UserStruct(login=form.cleaned_data['login']))[0]
                return HttpResponseRedirect(reverse('profile',args=[user.id]))
            except:
                bar.errors.append('Cannot edit user.')
    form = EditUserForm()
    user_list = User.filter(UserStruct())
    return render_to_response('users.html', {'page_info' : page_info, 'edit_form' : form, 'user_list' : user_list})
