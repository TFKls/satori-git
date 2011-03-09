# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

class ManageForm(forms.Form):
    name = forms.CharField(required=True)
    description = forms.CharField(required=False)
    viewing = forms.ChoiceField(label='Contest visible for',choices=[['none','Contestants only'],['auth','Logged users'],['anonym','Everyone']])
    joining = forms.ChoiceField(label='Joining method',choices=[['none','None (only admin-adding)'],['apply','Application'],['free','Free']])

class AdminForm(forms.Form):
    username = forms.CharField(required=True)

class RightsStatus(object):
    viewing = 'none'
    joining = 'none'
    auth = None
    anonum = None

def get_status(contest):
    status = RightsStatus()
    status.auth = Security.authenticated()
    status.anonym = Security.anonymous()
    if Privilege.get(status.anonym,contest,'VIEW'):
        status.viewing='anonym'
    elif Privilege.get(status.auth,contest,'VIEW'):
        status.viewing='auth'
    if Privilege.get(status.auth,contest,'JOIN'):
        status.joining = 'free'
    elif Privilege.get(status.auth,contest,'APPLY'):
        status.joining = 'apply'
    return status

@contest_view
def view(request, page_info):
    contest = page_info.contest
    status = get_status(contest)
    admins = [c.usernames for c in Web.get_contest_admins(contest=contest,offset=0,limit=500).contestants]
    if request.method!="POST":
        manage_form = ManageForm(initial={'viewing' : status.viewing, 'joining' : status.joining, 'name' : contest.name, 'description' : contest.description})
        admin_form = AdminForm()
        return render_to_response('manage.html', {'page_info' : page_info, 'manage_form' : manage_form, 'admin_form' : admin_form, 'admins' : admins})
    if "addadmin" in request.POST.keys():
        manage_form = ManageForm(initial={'viewing' : status.viewing, 'joining' : status.joining, 'name' : contest.name, 'description' : contest.description})
        admin_form = AdminForm(request.POST)
        if admin_form.is_valid():
            try:
                user = User.filter(UserStruct(login=admin_form.cleaned_data["username"]))[0]
                contest.add_admin(user)
            except:
                admin_form._errors['username'] = ['Adding failed!']
        return render_to_response('manage.html', {'page_info' : page_info, 'manage_form' : manage_form, 'admin_form' : admin_form, 'admins' : admins})
    admin_form = AdminForm()
    manage_form = ManageForm(request.POST)
    if not manage_form.is_valid():
        return render_to_response('manage.html', {'page_info' : page_info, 'manage_form' : manage_form, 'admin_form' : admin_form, 'admins' : admins})
    viewing = manage_form.cleaned_data['viewing']
    joining = manage_form.cleaned_data['joining']
    contest.name = manage_form.cleaned_data['name']
    contest.description = manage_form.cleaned_data['description']
    if status.viewing!=viewing:
        Privilege.revoke(status.auth,contest,'VIEW')
        Privilege.revoke(status.anonym,contest,'VIEW')
        if viewing=='anonym':
            Privilege.grant(status.anonym,contest,'VIEW')
        elif viewing=='auth':
            Privilege.grant(status.auth,contest,'VIEW')
    if status.joining!=joining:
        Privilege.revoke(status.auth,contest,'APPLY')
        Privilege.revoke(status.auth,contest,'JOIN')
        if joining=='apply':
            Privilege.grant(status.auth,contest,'APPLY')
        elif joining=='free':
            Privilege.grant(status.auth,contest,'JOIN')
    return render_to_response('manage.html', {'page_info' : page_info, 'manage_form' : manage_form, 'admin_form' : admin_form, 'admins' : admins})

