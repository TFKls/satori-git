# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.forms import AlertList
#from satori.web.utils.tables import *
from satori.web.utils.generic_table import GenericTable
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms



def accept(id,request,page_info):
    contestant = Contestant(int(id))
    contestant.accepted = True

def revoke(id,request,page_info):
    contestant = Contestant(int(id))
    contestant.accepted = False

def delete(id,request,page_info):
    contestant = Contestant(int(id))
    contestant.delete()

def hide(id,request,page_info):
    contestant = Contestant(int(id))
    contestant.invisible = True

def show(id,request,page_info):
    contestant = Contestant(int(id))
    contestant.invisible = False

def add(id,request,page_info):
    try:
        user = User.filter(UserStruct(login=request.POST['login_add']))[0]
        Contestant.create(ContestantStruct(contest=page_info.contest,accepted=True),[user])
        page_info.alerts.add('User added to contest.','success')
    except IndexError:
        page_info.alerts.add('User '+request.POST['login_add']+' not found.','danger')

def copy_contestants(id,request,page_info):
    contest = page_info.contest
    try:
        import_from = Contest(int(request.POST['copy_contest']))
        for contestant in Contestant.filter(ContestantStruct(contest=import_from)):
            try:
                Contestant.create(ContestantStruct(contest=contest, accepted=contestant.accepted, invisible=contestant.invisible, login=contestant.login), contestant.get_member_users())
            except AlreadyRegistered:
                page_info.alerts.add('User '+str(contestant.login)+' already in contest.','warning')
            
    except IndexError:
        page_info.alerts.add('Contest number "'+request.POST['copy_contest']+'" not found.','danger')
    except Exception as e:
        page_info.alerts.add('Operation failed: '+str(e)+'!','danger')

def process_post(request,page_info):
    operation_prefixes = [['revoke',revoke],['accept',accept],['delete',delete],['hide',hide],['show',show],
                          ['add',add],['copy_contestants',copy_contestants]                                 ]  # we search for 'operation_id' in POST.keys(), e.g. 'revoke_131'
                                                                                                                # we translate operation for one of the above functions, the integer for the object key
                                                                                                                # key 'mass' means that we perform the operation on all checked 'select_id' objects
    target_string = []
    page_info.alerts = AlertList()
    for field in request.POST.keys():
        for prefix in operation_prefixes:
            plen = len(prefix[0])
            if field[:plen]==prefix[0]:
                operation = prefix[1]
                target_string = field[plen+1:]
    if target_string=='mass':
        targets = []
        for field in request.POST.keys():
            if field[:6]=='select':
                targets.append(int(field[7:]))
    else:
        targets = [target_string]
    try:
        for element in targets:
            operation(element,request,page_info)
    except Exception as e:
        page_info.alerts.add('Operation failed: '+str(e)+'!','danger')

@contest_view
def view(request, page_info):
    if request.method=='POST':
        process_post(request,page_info)
    max_limit = 50000
    contest = page_info.contest
    contestants = GenericTable('contestants',request.GET)
    contestants.fields = ['name']
    raw_list = []
    contestants.accepted_status = contestants.my_params.get("accepted_status",None)
    contestants.visibility_status = contestants.my_params.get("visibility_status",None)
    visibility = None
    if contestants.visibility_status=='visible_only':
        visibility = False
    if contestants.visibility_status=='hidden_only':
        visibility = True
    if contestants.accepted_status!='pending_only':
        raw_list += Web.get_accepted_contestants(contest=contest,limit=max_limit).contestants
    if contestants.accepted_status!='accepted_only':
        raw_list += Web.get_pending_contestants(contest=contest,limit=max_limit).contestants
    contestants.allcontests = Contest.filter()
    contestants.allcontests.sort(key = lambda c : c.name)
    for c in raw_list:
        contestants.data.append({'id' : c.id, 'name' : c.name, 'accepted' : c.accepted, 'hidden' : c.invisible, 'members' : c.get_member_users()})
    contestants.fieldnames = [['name','name']]
#    contestants.filter_by_fields(['name'])
    contestants.default_sortfield = 'name'
    contestants.autosort()
    contestants.autopaginate()
    allcontests = Web.get_contest_list()
    return render_to_response('contestants.html', {'page_info' : page_info, 'contestants' : contestants, 'allcontests' : allcontests})



@contest_view
def viewteam(request, page_info, id = None):
    class ContestantForm(forms.Form):
        team_name = forms.CharField(required=True,label='Contestant name')
        accepted = forms.BooleanField(required=False,label='Accepted')
        invisible = forms.BooleanField(required=False,label='Hidden')
        
    class AddForm(forms.Form):
        login = forms.CharField(required=True,label='Add user')
        
    if not id:
        contestant = page_info.contestant
    else:
        contestant = Contestant(int(id))
    users = contestant.get_member_users()
    form = ContestantForm(data={'team_name' : contestant.name, 'accepted' : contestant.accepted, 'invisible' : contestant.invisible})
    add_form = AddForm()
    if request.method=="POST":
        if 'change' in request.POST:
            form = ContestantForm(request.POST)
            if form.is_valid():
                try:
                    data = form.cleaned_data
                    contestant.modify(ContestantStruct(name=data['team_name'],accepted=data['accepted'],invisible=data['invisible']))
                    return HttpResponseRedirect(reverse('contestant_view',args=[page_info.contest.id,id]))
                except:
                    pass
        if 'add' in request.POST:
            add_form = AddForm(request.POST)
            if add_form.is_valid():
                newuser = User.filter(UserStruct(login=add_form.cleaned_data['login']))[0]
                contestant.add_member_user(newuser)
                return HttpResponseRedirect(reverse('contestant_view',args=[page_info.contest.id,id]))
        for k in request.POST.keys():
            if k[:6]=="remove":
                uid = int(k[7:])
                newuser = User(uid)
                contestant.delete_member_user(newuser)
                return HttpResponseRedirect(reverse('contestant_view',args=[page_info.contest.id,id]))
    return render_to_response('teampage.html', {'page_info' : page_info, 'contestant' : contestant, 'users' : users, 'form' : form, 'add_form' : add_form})
