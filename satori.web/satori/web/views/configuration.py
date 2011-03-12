# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django import forms


class PSetterAddForm(forms.Form):
    login = forms.CharField(required = True)

@general_view
def view(request, page_info):
    if request.method=='POST' and 'add' in request.POST.keys():
        form = PSetterAddForm(data=request.POST)
        if form.is_valid():
            try:
                user = User.filter(UserStruct(login=form.cleaned_data['login']))[0]
                Privilege.global_grant(user,'MANAGE_PROBLEMS')
                form = PSetterAddForm()
            except:
                form._errors["login"] = ['Privilege grant failed!']
    else:
        form = PSetterAddForm()
    if request.method=='POST' and 'revoke' in request.POST.keys():
        user_id = request.POST['id']
        user = User(int(user_id))
        Privilege.global_revoke(user,'MANAGE_PROBLEMS')
    is_priv_admin = Privilege.global_demand('MANAGE_PRIVILEGES')
    if is_priv_admin:
        problem_setters = Privilege.global_list('MANAGE_PROBLEMS').keys()
    else:
        problem_setters = None
    return render_to_response('configuration.html', {'page_info' : page_info, 'problem_setters' : problem_setters, 'form' : form, 'is_priv_admin' : is_priv_admin})
