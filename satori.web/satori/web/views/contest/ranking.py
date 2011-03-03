# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils import xmlparams
from satori.web.utils.shortcuts import text2html
from django.shortcuts import render_to_response
from django import forms


@contest_view
def view(request, page_info, id):
    ranking = Ranking(int(id))
    return render_to_response('ranking.html', {'page_info' : page_info, 'ranking' : ranking, 'content' : text2html(ranking.full_ranking())})


class AddBaseForm(forms.Form):
    ranking_name = forms.CharField(label="Ranking name", required=True)
    ranking_is_public = forms.BooleanField(label="Public", required=False)


@contest_view
def add(request, page_info):
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
            Ranking.create(RankingStruct(contest=page_info.contest,name=base_form.cleaned_data["ranking_name"],aggregator=selected,is_public=base_form.cleaned_data["ranking_is_public"]),om.get_map(), {}, {})
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
    suites = ranking.get_problem_test_suites()
    problem_list = [ [p,suites.get(p,None)] for p in problems ]
    
        
    xml = " ".join([x[2:] for x in filter(lambda line:line.startswith("#@"),aggregators[ranking.aggregator].splitlines())])
    sections = xmlparams.ParseXML(xml)
    general = sections['general']
    if request.method=="POST":
        base_form = AddBaseForm(request.POST)
        form = xmlparams.ParamsForm(paramsdict=general,data=request.POST)
        if base_form.is_valid() and form.is_valid():
            om = general.dict_to_oa_map(form.cleaned_data)
            ranking.modify_full(RankingStruct(contest=page_info.contest,name=base_form.cleaned_data["ranking_name"],aggregator=ranking.aggregator,is_public=base_form.cleaned_data["ranking_is_public"]),om.get_map(), {}, {})
    else:
        base_form = AddBaseForm(initial={'ranking_name' : ranking.name, 'ranking_is_public' : ranking.is_public})
        form = xmlparams.ParamsForm(paramsdict=general,oamap=ranking.params_get_map())
        form.is_valid()
        d = form.fields.__dict__
    return render_to_response('ranking_edit.html', {'page_info' : page_info, 'base_form' : base_form, 'form' : form, 'problem_list' : problem_list})

@contest_view
def editparams(request, page_info, id):
    pass