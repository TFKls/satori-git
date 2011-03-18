# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django import forms
from datetime import datetime
from satori.web.utils.files import valid_attachments
from satori.web.utils.forms import SatoriDateTimeField
from satori.web.utils.shortcuts import text2html,fill_image_links

class ProblemsPublishForm(forms.Form):
    submitstart = SatoriDateTimeField(required=False)
    submitfinish = SatoriDateTimeField(required=False)
    viewauto = forms.BooleanField(required=False,initial=True)
    viewstart = SatoriDateTimeField(required=False)
    viewfinish = SatoriDateTimeField(required=False)
    def __init__(self,problem_list=[],data=None,*args,**kwargs):
        super(ProblemsPublishForm, self).__init__(data,*args, **kwargs)
        for pinfo in problem_list:
            if pinfo.is_admin:
                self.fields[str(pinfo.problem_mapping.id)] = forms.BooleanField(required=False)


def between(times, now):
    if not times:
        return False
    start = times.start_on
    finish = times.finish_on
    if not start and not finish:
        return True
    if not start and finish and finish>now:
        return True
    if not finish and start and start<now:
        return True
    if start and finish and start<now and finish>now:
        return True
    return False
    
@contest_view
def viewall(request, page_info):
    problem_list = Web.get_problem_mapping_list(page_info.contest)
    problem_list.sort(key=lambda p:p.problem_mapping.code)
    if request.method=="POST":
        form = ProblemsPublishForm(data=request.POST,problem_list=problem_list)
        if form.is_valid():
            data = form.cleaned_data
            selected = []
            role = page_info.contest.contestant_role
            for pinfo in problem_list:
                id = str(pinfo.problem_mapping.id)
                if id in request.POST.keys():
                    selected.append(pinfo.problem_mapping)
            if "changesubmit" in request.POST.keys():
                for s in selected:
                    start = data.get('submitstart',None)
                    finish = data.get('submitfinish',None)
                    Privilege.grant(role,s,'SUBMIT',PrivilegeTimes(start_on=start,finish_on=finish))
                    if 'viewauto' in request.POST.keys():
                        Privilege.grant(role,s,'VIEW',PrivilegeTimes(start_on=start))
            elif "changeview" in request.POST.keys():
                for s in selected:
                    start = data.get('viewstart',None)
                    finish = data.get('viewfinish',None)
                    Privilege.grant(role,s,'VIEW',PrivilegeTimes(start_on=start,finish_on=finish))
            elif "revokesubmit" in request.POST.keys():
                for s in selected:
                    Privilege.revoke(role,s,"SUBMIT")
            elif "revokeview" in request.POST.keys():
                for s in selected:
                    Privilege.revoke(role,s,"SUBMIT")
                    Privilege.revoke(role,s,"VIEW")
            problem_list = Web.get_problem_mapping_list(page_info.contest)
            problem_list.sort(key=lambda p:p.problem_mapping.code)
    else:
        form = ProblemsPublishForm(problem_list=problem_list)
    problems = []
    any_admin = False
    groups = {}
    for pinfo in problem_list:
        p = {}
        admin = pinfo.is_admin
        p['problem'] = pinfo.problem_mapping
        p['admin'] = admin
        p['has_pdf'] = pinfo.has_pdf
        p['description'] = text2html(pinfo.problem_mapping.description)
        g = pinfo.problem_mapping.group
        if not g in groups.keys():
            groups[g] = []
        if admin:
            any_admin = True
            p['select'] = form[str(pinfo.problem_mapping.id)]
            p['visible'] = between(pinfo.contestant_role_view_times,datetime.now())
            p['submittable'] = between(pinfo.contestant_role_submit_times,datetime.now())
            p['when_view'] = pinfo.contestant_role_view_times
            p['when_submit'] = pinfo.contestant_role_submit_times
            
        groups[g].append(p)
    return render_to_response('problems.html', { 'page_info' : page_info, 'form' : form, 'problems' : problems, 'any_admin' : any_admin, 'groups' : groups })

class ProblemAddForm(forms.Form):
    code = forms.CharField(required=True)
    title = forms.CharField(required=True)
    description = forms.CharField(required=False, label='Additional comment')
    group = forms.CharField(required=False)
    suite = forms.ChoiceField(choices=[])
    statement = forms.CharField(widget=forms.Textarea, required=False)
    pdf = forms.FileField(required=False)
    fid = forms.CharField(required=True, widget=forms.HiddenInput) # (temporary) folder id
    def __init__(self,data=None,suites=[],*args,**kwargs):
        super(ProblemAddForm,self).__init__(data,*args,**kwargs)
        self.fields["suite"].choices = [[suite.id,suite.name + '(' + suite.description + ')'] for suite in suites]


@contest_view
def add(request, page_info):
    if 'preid' in request.GET.keys():
        preid = request.GET["preid"]
        problem = Problem(int(preid))
        suites = TestSuite.filter(TestSuiteStruct(problem=problem))
            
        if request.method=="POST":
            form = ProblemAddForm(data=request.POST,files=request.FILES,suites=suites)
            if form.is_valid():
                data = form.cleaned_data
                fid = data['fid']
                suite = filter(lambda s:s.id==int(data["suite"]),suites)[0]
                mapping = ProblemMapping.create(ProblemMappingStruct(contest=page_info.contest,
                                                                     problem=problem,
                                                                     code=data['code'],
                                                                     title=data['title'],
                                                                     group=data['group'],
                                                                     statement='',
                                                                     description=data['description'],
                                                                     default_test_suite=suite))
                pdf = form.cleaned_data.get('pdf',None)
                if pdf:
                    writer = Blob.create(pdf.size)
                    writer.write(pdf.read())
                    phash = writer.close()
                    mapping.statement_files_set_blob_hash('pdf',phash)
                    mapping.statement_files_set_blob_hash('_pdf',phash)

                for ufile in glob.glob(os.path.join(fid, '*')):
                    mapping.statement_files_set_blob_path(os.path.basename(ufile), ufile)
                try:
                    mapping.statement = data['statement']
                except SphinxException as sphinxException:
                    return render_to_response('problems_add.html', { 'fid' : fid,
                                                                     'form' : form, 
                                                                     'page_info' : page_info,
                                                                     'sphinxException' : sphinxException })
                return HttpResponseRedirect(reverse('contest_problems', args=[page_info.contest.id]))
        else:
            #TODO(kalq): Create a hash instead of full pathname
            fid = tempfile.mkdtemp()
            form = ProblemAddForm(suites=suites, initial={ 'fid' : fid })
            return render_to_response('problems_add.html', { 'page_info' : page_info,
                                                             'fid' : fid,
                                                             'form' : form,
                                                             'base' : problem } )
    else:
        problems = Problem.filter()
        choices = [[problem.id, problem.name + '(' + problem.description + ')'] for problem in problems]

        class ProblemPreAddForm(forms.Form):
            preid = forms.ChoiceField(choices=choices,label='Use problem')
        
        form = ProblemPreAddForm()
        return render_to_response('problems_add.html', { 'page_info' : page_info, 'form' : form } )
        
@contest_view
def edit(request, page_info, id):
    mapping = ProblemMapping(int(id))
    problem = mapping.problem
    suites = TestSuite.filter(TestSuiteStruct(problem=problem))
    if request.method=="POST":
        form = ProblemAddForm(data=request.POST,files=request.FILES,suites=suites)
        if form.is_valid():
            data = form.cleaned_data
            fid = data['fid']
            for rfile in request.POST:
                if rfile.startswith('rfile'):
                    mapping.statement_files_delete(request.POST[rfile])
            for ufile in glob.glob(os.path.join(fid, '*')):
                mapping.statement_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                mapping.modify(ProblemMappingStruct(code=data['code'],
                                                    title=data['title'],
                                                    statement=data['statement'],
                                                    group=data['group'],
                                                    description=data['description'],
                                                    default_test_suite=TestSuite(int(data['suite']))))
            except SphinxException as sphinxException:
                attachments = valid_attachments(mapping.statement_files_get_list())
                return render_to_response('problems_add.html', { 'attachments' : attachments,
                                                                 'fid' : fid,
                                                                 'form' : form,
                                                                 'page_info' : page_info,
                                                                 'sphinxException' : sphinxException,
                                                                 'base' : problem,
                                                                 'editing' : mapping })
            pdf = form.cleaned_data.get('pdf',None)
            if pdf:
                writer = Blob.create(pdf.size)
                writer.write(pdf.read())
                phash = writer.close()
                mapping.statement_files_set_blob_hash('pdf',phash)
                mapping.statement_files_set_blob_hash('_pdf',phash)
            return HttpResponseRedirect(reverse('contest_problems', args=[page_info.contest.id]))
    else:
        fid = tempfile.mkdtemp()
        form = ProblemAddForm(initial={ 'code' : mapping.code,
                                        'title' : mapping.title,
                                        'statement' : mapping.statement,
                                        'description' : mapping.description,
                                        'group' : mapping.group,
                                        'fid' : fid,
                                        'suite' : mapping.default_test_suite.id }, suites=suites)
    attachments = valid_attachments(mapping.statement_files_get_list())
    return render_to_response('problems_add.html', { 'attachments' : attachments,
                                                     'page_info' : page_info,
                                                     'fid' : fid,
                                                     'form' : form,
                                                     'base' : problem,
                                                     'editing' : mapping })

@contest_view
def view(request, page_info, id):
    problem = Web.get_problem_mapping_info(ProblemMapping(int(id)))
    content = fill_image_links(problem.html,'ProblemMapping',id, 'statement_files')
    return render_to_response('problems_view.html', {'page_info' : page_info, 'problem' : problem, 'content' : content })
    
