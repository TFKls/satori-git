# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.generic_table import GenericTable
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

@general_view
def view(request, page_info):
    users = GenericTable('users',request.GET)
    users.fields = ['login', 'firstname', 'lastname', 'affiliation', 'email']
    for user in User.filter(UserStruct()):
        users.data.append({'login' : user.login, 'firstname' : user.firstname, 'lastname' : user.lastname, 'email' : user.email, 'id' : user.id, 'affiliation' : user.affiliation})
    users.filter_by_fields(users.fields)    
    users.fieldnames = [['login','login'], ['firstname','first name'],['lastname','last name'],['email','e-mail'],['affiliation','affiliation']]
    users.default_sortfield='lastname'
    users.autosort()
    users.autopaginate()
    return render_to_response('users.html', {'page_info' : page_info, 'users' : users})
