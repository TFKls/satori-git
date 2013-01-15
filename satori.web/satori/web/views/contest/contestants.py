# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.forms import StatusBar
from satori.web.utils.tables import *
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
    contest = page_info.contest
    
    class AcceptedTable(ResultTable):
        @staticmethod
        def default_limit():
            return 20
        def length(self):
            return len(self.contestants)


        def __init__(self,req,prefix,get_function,button_prefix):
            super(AcceptedTable,self).__init__(req=req,prefix=prefix,autosort=False)
            page = self.params['page']
            limit = self.params['limit']
            query = get_function(contest=contest,offset=(page-1)*limit,limit=limit)
            self.contestants = query.contestants
            self.total = query.count
            self.button_prefix = button_prefix
    
            self.fields.append(TableField( name ='',
                            value = lambda table, i : 'check',
                            render = lambda table, i : format_html(u'<input type="checkbox" name="{0}{1}"/>', table.button_prefix, table.contestants[i].id),
                            sortable = False, id = 1 ))
            self.fields.append(TableField( name='Team name', value= lambda table,i: table.contestants[i].name,
                                                             render = lambda table,i: format_html(u'<a class="stdlink" href="{0}">{1}</a>', reverse('contestant_view',args=[contest.id,table.contestants[i].id]), table.contestants[i].name),
                                                             id=2 ))
            self.fields.append(TableField( name='Users',value=(lambda table,i: table.contestants[i].usernames), id=3 ))

    class ImportForm(forms.Form):
        contest = forms.ChoiceField(choices=[[c.contest.id, c.contest.name] for c in Web.get_contest_list() if c.is_admin and c.contest.id != page_info.contest.id], required=True)
            
    accepted = AcceptedTable(req=request.GET,prefix='accepted',get_function=Web.get_accepted_contestants,button_prefix='revoke_')
    pending = AcceptedTable(req=request.GET,prefix='pending',get_function=Web.get_pending_contestants,button_prefix='accept_')
    add_form = ManualAddForm()
    import_form = ImportForm()
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
        if "import" in request.POST.keys():
            import_form = ImportForm(request.POST)
            if import_form.is_valid():
                import_from = Contest(int(import_form.cleaned_data["contest"]))
                for contestant in Contestant.filter(ContestantStruct(contest=import_from)):
                    try:
                        Contestant.create(ContestantStruct(contest=contest, accepted=contestant.accepted, invisible=contestant.invisible, login=contestant.login, password=contestant.password), contestant.get_member_users())
                    except AlreadyRegistered:
                        pass
        return HttpResponseRedirect(reverse('contestants',args=[contest.id]))
    return render_to_response('contestants.html', {'page_info' : page_info, 'accepted' : accepted, 'pending' : pending, 'add_form' : add_form, 'import_form' : import_form, 'status_bar' : bar })

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
