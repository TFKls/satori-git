# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.forms import StatusBar
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

class ManualAddForm(forms.Form):
    user = forms.CharField(required=False, label="Login")
    def clean(self):
        data = self.cleaned_data
        try:
            data['user'] = User.filter(UserStruct(login=data['user']))[0]
        except:
            raise forms.ValidationError('User not found!')
            del data['user']
        return data

@contest_view
def view(request, page_info):
    limit = 25
    page1 = int(request.GET.get('page1',0))
    page2 = int(request.GET.get('page2',0))
    contest = page_info.contest
    accepted = Web.get_accepted_contestants(contest=contest,offset=page1*limit,limit=limit)
    count1 = (accepted.count+limit-1)/limit
    pending = Web.get_pending_contestants(contest=contest,offset=page2*limit, limit=limit)
    count2 = (pending.count+limit-1)/limit
    page_params = {'page1' : page1, 'page2' : page2, 'loop1' : range(0,count1), 'loop2' : range(0,count2), 'count1' : count1, 'count2' : count2}
    add_form = ManualAddForm()
    bar = None
    if request.method=="POST":
        if 'accept' in request.POST.keys():
            for contestant in pending.contestants:
                if 'accept_'+str(contestant.id) in request.POST.keys():
                    contestant.accepted = True
        if 'dismiss' in request.POST.keys():
            for contestant in pending.contestants:
                if 'accept_'+str(contestant.id) in request.POST.keys():
                    try:
                        contestant.delete()
                    except CannotDeleteObject:
                        bar = StatusBar()
                        bar.errors.append('Cannot delete '+contestant.name+' may have already submitted.')
        if 'revoke' in request.POST.keys():
            for contestant in accepted.contestants:
                if 'revoke_'+str(contestant.id) in request.POST.keys():
                    contestant.accepted = False
        if 'hide' in request.POST.keys():
            for contestant in accepted.contestants:
                if 'revoke_'+str(contestant.id) in request.POST.keys():
                    contestant.invisible = True        
        if 'show' in request.POST.keys():
            for contestant in accepted.contestants:
                if 'revoke_'+str(contestant.id) in request.POST.keys():
                    contestant.invisible = False        
        if 'add' in request.POST.keys():
            add_form = ManualAddForm(request.POST)
            if add_form.is_valid():
                Contestant.create(ContestantStruct(contest=contest,accepted=True),[add_form.cleaned_data['user']])
        return HttpResponseRedirect(reverse('contestants',args=[contest.id]))
    return render_to_response('contestants.html', {'page_info' : page_info, 'accepted' : accepted, 'pending' : pending, 'add_form' : add_form, 'page_params' : page_params, 'status_bar' : bar })

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
