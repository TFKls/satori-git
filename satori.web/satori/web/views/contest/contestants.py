# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

class ManualAddForm(forms.Form):
    user = forms.CharField(required=False, label="Add user manually")
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
    limit = 10
    page1 = int(request.GET.get('page1',0))
    page2 = int(request.GET.get('page2',0))
    contest = page_info.contest
    accepted = contest.get_contestants(offset=page1*limit,limit=limit)
    count1 = (accepted.count+limit-1)/limit
    pending = contest.get_pending_contestants(offset=page2*limit, limit=limit)
    count2 = (pending.count+limit-1)/limit
    page_params = {'page1' : page1, 'page2' : page2, 'loop1' : range(0,count1), 'loop2' : range(0,count2)}
    add_form = ManualAddForm()
    if request.method=="POST":
        if 'accept' in request.POST.keys():
            for cinfo in pending.contestants:
                contestant = cinfo.contestant
                if 'accept_'+str(contestant.id) in request.POST.keys():
                    contestant.accepted = True
        if 'revoke' in request.POST.keys():
            for cinfo in accepted.contestants:
                contestant = cinfo.contestant
                if 'revoke_'+str(contestant.id) in request.POST.keys():
                    contestant.accepted = False
        if 'add' in request.POST.keys():
            add_form = ManualAddForm(request.POST)
            if add_form.is_valid():
                Contestant.create(ContestantStruct(contest=contest,accepted=True),[add_form.cleaned_data['user']])
        accepted = contest.get_contestants(offset=page1*limit,limit=limit)
        pending = contest.get_pending_contestants(offset=page2*limit, limit=limit)
    return render_to_response('contestants.html', {'page_info' : page_info, 'accepted' : accepted, 'pending' : pending, 'add_form' : add_form, 'page_params' : page_params })
