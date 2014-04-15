# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import StatusBar
from satori.web.utils.generic_table import GenericTable
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

class EditUserForm(forms.Form):
    login = forms.CharField(required=True,label='User login:')

@general_view
def view(request, page_info):
    users = GenericTable('users',request.GET)
    for user in User.filter(UserStruct()):
        users.data.append({'login' : user.login, 'firstname' : user.firstname, 'lastname' : user.lastname, 'email' : user.email})
    users.autosort()
    users.autopaginate()
    return render_to_response('users.html', {'page_info' : page_info, 'users' : users})
