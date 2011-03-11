# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils import xmlparams
from satori.web.utils.shortcuts import text2html
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms


@contest_view
def view(request, page_info, id):
    ranking = Ranking(int(id))
    return render_to_response('ranking.html', {'page_info' : page_info, 'ranking' : ranking, 'content' : text2html(ranking.full_ranking())})


class AddBaseForm(forms.Form):
    ranking_name = forms.CharField(label="Ranking name", required=True)
    ranking_visibility = forms.ChoiceField(label="Ranking visible for", required=True, choices=[['admin','Admins only'],['contestant','Contestants'],['public', 'Everyone']])

@contest_view
def add(request, page_info):
    contest = page_info.contest
    aggregators = Global.get_aggregators()

    class AddSimpleForm(forms.Form):
        selected=forms.ChoiceField(choices=[[a,a] for a in aggregators.keys()],label="Select ranking type")
                
    selected = request.GET.get("selected",None)
    if not selected:
        form = AddSimpleForm()
        return render_to_response('ranking_add.html', {'page_info' : page_info, 'form' : form})
        
    xml = " ".join([x[2:] for x in filter(lambda line:line.startswith("#@"),aggregators[selected].splitlines())])
    sections = xmlparams.ParseXML(xml)
    general = sections['general']
    if request.method=="POST":
        base_form = AddBaseForm(request.POST)
        form = xmlparams.ParamsForm(paramsdict=general,data=request.POST)
        if base_form.is_valid() and form.is_valid():
            om = general.dict_to_oa_map(form.cleaned_data)            
            ranking = Ranking.create(RankingStruct(contest=page_info.contest,name=base_form.cleaned_data["ranking_name"],aggregator=selected,is_public=False),om.get_map(), {}, {})
            newvis = base_form.cleaned_data["ranking_visibility"]
            if newvis=='public':
                Privilege.grant(contest.contestant_role,ranking,'VIEW_FULL')
                Privilege.grant(contest.contestant_role,ranking,'VIEW')
                public = True
            elif newvis=='contestant':
                Privilege.grant(contest.contestant_role,ranking,'VIEW_FULL')
                Privilege.grant(contest.contestant_role,ranking,'VIEW')
                public = False
            else:
                Privilege.revoke(contest.contestant_role,ranking,'VIEW_FULL')
                Privilege.revoke(contest.contestant_role,ranking,'VIEW')
                public = False                    
            ranking.is_public = public
            return HttpResponseRedirect(reverse('ranking_edit',args=[contest.id,ranking.id]))
    else:
        base_form = AddBaseForm()
        form = xmlparams.ParamsForm(general)
    return render_to_response('ranking_add.html', {'page_info' : page_info, 'base_form' : base_form, 'form' : form, 'selected' : selected})


@contest_view
def edit(request, page_info, id):
    aggregators = Global.get_aggregators()
    ranking = Ranking(int(id))
    contest = page_info.contest
    problems = ProblemMapping.filter(ProblemMappingStruct(contest=contest))
    problems.sort(key=lambda p : p.code)
    suites = dict([[k.id, v] for k, v in ranking.get_problem_test_suites().iteritems()])
    problem_params = dict([[k.id, v] for k, v in ranking.get_problem_params().iteritems()])
    problem_list = [ [p,suites.get(p.id,None),problem_params.get(p.id,None)] for p in problems ]
    if ranking.is_public:
        visibility = 'public'
    elif Privilege.get(contest.contestant_role,ranking,'VIEW'):
        visibility = 'contestant'
    else:
        visibility = 'admin'        
    xml = " ".join([x[2:] for x in filter(lambda line:line.startswith("#@"),aggregators[ranking.aggregator].splitlines())])
    sections = xmlparams.ParseXML(xml)
    general = sections['general']
    if request.method=="POST":
        base_form = AddBaseForm(request.POST)
        form = xmlparams.ParamsForm(paramsdict=general,data=request.POST)
        if base_form.is_valid() and form.is_valid():
            om = general.dict_to_oa_map(form.cleaned_data)
            newvis = base_form.cleaned_data["ranking_visibility"]
            public = ranking.is_public
            if newvis != visibility:
                if newvis=='public':
                    Privilege.grant(contest.contestant_role,ranking,'VIEW_FULL')
                    Privilege.grant(contest.contestant_role,ranking,'VIEW')
                    public = True
                elif newvis=='contestant':
                    Privilege.grant(contest.contestant_role,ranking,'VIEW_FULL')
                    Privilege.grant(contest.contestant_role,ranking,'VIEW')
                    public = False
                else:
                    Privilege.revoke(contest.contestant_role,ranking,'VIEW_FULL')
                    Privilege.revoke(contest.contestant_role,ranking,'VIEW')
                    public = False                    
            ranking.modify_full(RankingStruct(contest=page_info.contest,name=base_form.cleaned_data["ranking_name"],aggregator=ranking.aggregator,is_public=public),om.get_map(), {}, {})
            return HttpResponseRedirect(reverse('ranking_edit',args=[contest.id,id]))
    else:
        base_form = AddBaseForm(initial={'ranking_name' : ranking.name, 'ranking_visibility' : visibility})
        form = xmlparams.ParamsForm(paramsdict=general,oamap=ranking.params_get_map())
    return render_to_response('ranking_edit.html', {'page_info' : page_info, 'ranking' : ranking, 'base_form' : base_form, 'form' : form, 'problem_list' : problem_list})


@contest_view
def editparams(request, page_info, id, problem_id):
    aggregators = Global.get_aggregators()
    ranking = Ranking(int(id))
    contest = page_info.contest
    problem = ProblemMapping.filter(ProblemMappingStruct(id=int(problem_id)))[0]
    allparams = ranking.get_problem_params()
    params = None
    for k, v in allparams.iteritems():
        if k.id==int(problem_id):
            params = v
    xml = " ".join([x[2:] for x in filter(lambda line:line.startswith("#@"),aggregators[ranking.aggregator].splitlines())])
    sections = xmlparams.ParseXML(xml)
    general = sections['problem']    
    if request.method=="POST":
        form = xmlparams.ParamsForm(paramsdict=general,data=request.POST)
        if form.is_valid():
            om = general.dict_to_oa_map(form.cleaned_data)
            ranking.set_problem_params({problem : om.get_map()})
    else:
        form = xmlparams.ParamsForm(paramsdict=general,oamap=params)
    return render_to_response('ranking_editparams.html', {'page_info' : page_info, 'ranking' : ranking, 'form' : form})
