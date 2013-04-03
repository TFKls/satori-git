# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.tools import params
from satori.web.utils.files import valid_attachments
from satori.web.utils.decorators import contest_view
from satori.web.utils import xmlparams,rights
from satori.web.utils.shortcuts import text2html
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms


@contest_view
def view(request, page_info, id):
    contest = page_info.contest
    ranking = Ranking(int(id))
    if page_info.contest_is_admin:
        visible = Privilege.get(contest.contestant_role,ranking,'VIEW_FULL') or Privilege.get(Security.anonymous(),ranking,'VIEW_FULL') or Privilege.get(Security.authenticated(),ranking,'VIEW_FULL')
    else:
        visible = None
    if request.GET.get('fullscreen','0')!='0':
        template = 'ranking_fs.html'
    else:
        template = 'ranking.html'
    return render_to_response(template, {'page_info' : page_info, 'ranking' : ranking, 'visible' : visible, 'content' : text2html(ranking.full_ranking())})





@contest_view
def add(request, page_info):
    contest = page_info.contest
    aggregators = Global.get_aggregators()
    class AddForm(forms.Form):
        ranking_name = forms.CharField(label="Ranking name", required=True)
        selected = forms.ChoiceField(choices=[[a,a] for a in aggregators.keys()],label="Select ranking type")
        
    form = AddForm()            
    if request.method=="POST":
        form = AddForm(request.POST)
        if form.is_valid():
            ranking = Ranking.create(RankingStruct(contest=page_info.contest,name=form.cleaned_data["ranking_name"],aggregator=form.cleaned_data["selected"]),{},{},{})        
            return HttpResponseRedirect(reverse('ranking_edit',args=[contest.id,ranking.id]))
    return render_to_response('ranking_add.html', {'page_info' : page_info, 'form' : form})
        

@contest_view
def edit(request, page_info, id):
    massedit = request.GET.get('massedit',None)
    aggregators = Global.get_aggregators()
    ranking = Ranking(int(id))
    contest = page_info.contest
    problems = ProblemMapping.filter(ProblemMappingStruct(contest=contest))
    problems.sort(key=lambda p : p.code)
    suites_raw = ranking.get_problem_test_suites()
    params_raw = ranking.get_problem_params()
    stylesheet = ranking.presentation_get("stylesheet")
    suites = dict([[k.id, v] for k, v in suites_raw.iteritems()])
    problem_params = dict([[k.id, v] for k, v in params_raw.iteritems()])
    problem_list = [ [p,suites.get(p.id,None),problem_params.get(p.id,None)] for p in problems ]
    
    rightfield = rights.RightsTower(label="Visible for")
    rightfield.choices = ['Everyone','Contestants','Admins only']
    rightfield.roles = [Security.anonymous(),contest.contestant_role,None]
    rightfield.objects = [ranking,ranking,None]
    rightfield.rights = ['VIEW_FULL','VIEW_FULL','']
    rightfield.check()
    
    class EditBaseForm(forms.Form):
        name = forms.CharField(label="Ranking name", required=True)
        stylesheet = forms.FileField(required=False)
        visibility = rightfield.field()

    parser = params.parser_from_xml(description=aggregators[ranking.aggregator],section='aggregator',subsection='general')
    if request.method=="POST":
        if 'delete' in request.POST.keys():
            ranking.delete()
            return HttpResponseRedirect(reverse('contest_manage',args=[contest.id]))
        if 'remove_css' in request.POST.keys():
            ranking.presentation_delete('stylesheet')
            return HttpResponseRedirect(reverse('ranking_edit',args=[contest.id,id]))
        base_form = EditBaseForm(data=request.POST,files=request.FILES)
        form = xmlparams.ParamsForm(parser=parser,data=request.POST)
        if base_form.is_valid() and form.is_valid():
            ranking.modify_full(RankingStruct(contest=page_info.contest,name=base_form.cleaned_data["name"],aggregator=ranking.aggregator),parser.write_oa_map(form.cleaned_data), suites_raw, params_raw)
            rightfield.set(base_form.cleaned_data["visibility"])
            css = base_form.cleaned_data.get("stylesheet",None)
            data = base_form.cleaned_data
            if css:
                writer = Blob.create(css.size)
                writer.write(css.read())
                phash = writer.close()
                ranking.presentation_set_blob_hash('stylesheet',phash)
            return HttpResponseRedirect(reverse('ranking_edit',args=[contest.id,id]))
    else:
        base_form = EditBaseForm(initial={'name' : ranking.name, 'visibility' : unicode(rightfield.current)})
        form = xmlparams.ParamsForm(parser=parser,initial=parser.read_oa_map(ranking.params_get_map(),check_required=False))
    return render_to_response('ranking_edit.html', {'page_info' : page_info, 'ranking' : ranking, 'base_form' : base_form, 'form' : form, 'problem_list' : problem_list,'stylesheet' : stylesheet})



@contest_view
def editparams(request, page_info, id, problem_id):
    aggregators = Global.get_aggregators()
    ranking = Ranking(int(id))
    contest = page_info.contest
    problem = ProblemMapping(int(problem_id))
    allparams = ranking.get_problem_params()
    allsuites = ranking.get_problem_test_suites()
    problem_params = {}
    for k, v in allparams.iteritems():
        if k.id==int(problem_id):
            problem_params = v
    current_suite = None
    for k, v in allsuites.iteritems():
        if k.id==int(problem_id):
            current_suite = v
    
    class ParamsBaseForm(forms.Form):
        suite = forms.ChoiceField(choices=[[0,'Use default']]+[[s.id,s.name] for s in TestSuite.filter(TestSuiteStruct(problem=problem.problem))],label='Test suite')
    suiteid=0
    if current_suite:
        suiteid = current_suite.id
    parser = params.parser_from_xml(description=aggregators[ranking.aggregator],section='aggregator',subsection='problem')
    if request.method=="POST":
        if 'erase' in request.POST.keys():
            ranking.modify_problem(problem=problem,test_suite=None,params={})
            ranking.rejudge()
            return HttpResponseRedirect(reverse('ranking_edit',args=[page_info.contest.id,ranking.id]))
        base_form = ParamsBaseForm(data=request.POST)
        form = xmlparams.ParamsForm(parser=parser,data=request.POST)
        if base_form.is_valid() and form.is_valid():            
            data = base_form.cleaned_data
            if int(base_form.cleaned_data['suite'])==0:
                newsuite = None
            else:
                newsuite = TestSuite(int(base_form.cleaned_data['suite']))
#            ranking.set_problem_test_suites({problem : newsuite})
#            ranking.set_problem_params({problem : parser.write_oa_map(form.cleaned_data)})
            ranking.modify_problem(problem=problem,test_suite=newsuite,params=parser.write_oa_map(form.cleaned_data))
            ranking.rejudge()
            return HttpResponseRedirect(reverse('ranking_edit',args=[page_info.contest.id,ranking.id]))
    else:
        base_form = ParamsBaseForm(initial={'suite' : suiteid})
        form = xmlparams.ParamsForm(parser=parser,initial=parser.read_oa_map(problem_params,check_required=False))
    return render_to_response('ranking_editparams.html', {'page_info' : page_info, 'ranking' : ranking, 'form' : form, 'base_form' : base_form, 'problem' : problem})
    
@contest_view
def rejudge(request, page_info, id):
    ranking = Ranking(int(id))
    ranking.rejudge()
    return HttpResponseRedirect(reverse('contest_manage',args=[page_info.contest.id]))
    