# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.rights import RightsTower
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms
from satori.web.utils.forms import SatoriDateTimeField


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
    admins =  Web.get_contest_admins(contest=contest,offset=0,limit=500).contestants
    questions = Privilege.get(contest.contestant_role,contest,'ASK_QUESTIONS')
    backups = Privilege.get(contest.contestant_role,contest,'PERMIT_BACKUP')
    prints = Privilege.get(contest.contestant_role,contest,'PERMIT_PRINT')
    locks = Privilege.global_demand('MANAGE_LOCKS')
    anonym = Security.anonymous()
    auth = Security.authenticated()
    
    viewing = RightsTower(label='Contest visible for')
    viewing.add(anonym,contest,'VIEW','Everyone')
    viewing.add(auth,contest,'VIEW','Logged users')
    viewing.add(None,None,'','Contestants only')
    viewing.check()
    
    joining = RightsTower(label='Joining method')
    joining.add(auth,contest,'JOIN','Free')
    joining.add(auth,contest,'APPLY','Application')
    joining.add(None,None,'','Admin-adding only')
    joining.check()
    
    class ManageForm(forms.Form):
        name = forms.CharField(required=True)
        description = forms.CharField(required=False)
        if locks:
          lock_start = SatoriDateTimeField(required=False)
          lock_finish = SatoriDateTimeField(required=False)
          lock_address = forms.IPAddressField(required=False)
          lock_netmask = forms.IPAddressField(required=False)
        viewfield = viewing.field()
        joinfield = joining.field()
        questions = forms.BooleanField(label='Questions allowed',required=False)
        backups = forms.BooleanField(label='Backups allowed',required=False)            
        prints = forms.BooleanField(label='Prints allowed',required=False)            
    
    if request.method!="POST":
        def get_date(x):
            if x:
                return x.date()
            return None
        def get_time(x):
            if x:
                return x.time()
            return None
        manage_form = ManageForm(data={'viewfield' : unicode(viewing.current), 'joinfield' : unicode(joining.current), 'name' : contest.name, 'description' : contest.description, 'lock_start_0' : get_date(contest.lock_start), 'lock_start_1' : get_time(contest.lock_start), 'lock_finish_0' : get_date(contest.lock_finish),'lock_finish_1' : get_time(contest.lock_finish), 'lock_address' : contest.lock_address, 'lock_netmask' : contest.lock_netmask, 'questions' : questions, 'backups' : backups, 'prints' : prints})
        admin_form = AdminForm()
        return render_to_response('manage.html', {'page_info' : page_info, 'manage_form' : manage_form, 'admin_form' : admin_form, 'admins' : admins})
    if "addadmin" in request.POST.keys():
        admin_form = AdminForm(request.POST)
        if admin_form.is_valid():
            try:
                user = User.filter(UserStruct(login=admin_form.cleaned_data["username"]))[0]
                contest.add_admin(user)
                return HttpResponseRedirect(reverse('contest_manage',args=[page_info.contest.id]))
            except:
                admin_form._errors['username'] = ['Adding failed!']
        return HttpResponseRedirect(reverse('contest_manage',args=[contest.id]))
    if "revokeadmin" in request.POST.keys():
        user = Role(int(request.POST['adminid']))
        contest.delete_admin(user)
        return HttpResponseRedirect(reverse('contest_manage',args=[contest.id]))
    if "archive" in request.POST.keys():
        contest.modify(ContestStruct(archived=True))
        return HttpResponseRedirect(reverse('contest_manage',args=[contest.id]))
    if "unarchive" in request.POST.keys():
        contest.modify(ContestStruct(archived=False))
        return HttpResponseRedirect(reverse('contest_manage',args=[contest.id]))
    admin_form = AdminForm()
    manage_form = ManageForm(request.POST)
    if not manage_form.is_valid():
        return render_to_response('manage.html', {'page_info' : page_info, 'manage_form' : manage_form, 'admin_form' : admin_form, 'admins' : admins})
    viewing.set(manage_form.cleaned_data['viewfield'])
    joining.set(manage_form.cleaned_data['joinfield'])
    contest.name = manage_form.cleaned_data['name']
    contest.description = manage_form.cleaned_data['description']
    if locks:
        contest.lock_start = manage_form.cleaned_data['lock_start']
        contest.lock_finish = manage_form.cleaned_data['lock_finish']
        contest.lock_address = manage_form.cleaned_data['lock_address']
        contest.lock_netmask = manage_form.cleaned_data['lock_netmask']
    if manage_form.cleaned_data['questions']:
        Privilege.grant(contest.contestant_role,contest,'ASK_QUESTIONS')
    else:
        Privilege.revoke(contest.contestant_role,contest,'ASK_QUESTIONS')    
    if manage_form.cleaned_data['backups']:
        Privilege.grant(contest.contestant_role,contest,'PERMIT_BACKUP')
    else:
        Privilege.revoke(contest.contestant_role,contest,'PERMIT_BACKUP')    
    if manage_form.cleaned_data['prints']:
        Privilege.grant(contest.contestant_role,contest,'PERMIT_PRINT')
    else:
        Privilege.revoke(contest.contestant_role,contest,'PERMIT_PRINT')    
    return render_to_response('manage.html', {'page_info' : page_info, 'manage_form' : manage_form, 'admin_form' : admin_form, 'admins' : admins})

