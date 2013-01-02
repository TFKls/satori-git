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
from satori.web.utils.forms import SatoriDateTimeField, SatoriSignedField
from satori.web.utils.tables import *
from satori.web.utils.shortcuts import text2html,fill_image_links

    

class ProblemAddForm(forms.Form):
    code = forms.CharField(required=True)
    title = forms.CharField(required=True)
    description = forms.CharField(required=False, label='Additional comment')
    group = forms.CharField(required=False)
    suite = forms.ChoiceField(choices=[])
    statement = forms.CharField(widget=forms.Textarea, required=False)
    pdf = forms.FileField(required=False)
    fid = SatoriSignedField(required=True) # (temporary) folder id
    def __init__(self,data=None,suites=[],*args,**kwargs):
        super(ProblemAddForm,self).__init__(data,*args,**kwargs)
        self.fields["suite"].choices = [[suite.id,suite.name + '(' + suite.description + ')'] for suite in suites]


@contest_view
def add_choose(request,page_info):
    class ProblemsTable(ResultTable):
        def length(self):
            return len(self.problems)
                
        @staticmethod
        def default_limit():
            return 50
                                
        def __init__(self,req,prefix=''):
            super(ProblemsTable,self).__init__(req=req,prefix=prefix,autosort=True)
            self.problems = Problem.filter(ProblemStruct())
            self.total = len(self.problems)
            self.fields.append(TableField(name='Name',value=(lambda table,i: table.problems[i].name), 
                                          render=(lambda table,i : format_html(u'<a class="stdlink" href="{0}">{1}</a>',
                                              reverse('contest_problems_add_selected', args=[page_info.contest.id,table.problems[i].id]),
                                              table.problems[i].name)),
                                          id=3,css='link'))
            self.fields.append(TableField(name='Description',value=(lambda table,i: table.problems[i].description), id=2, css='description'))
            
    problem_list = ProblemsTable(request.GET,'problems')
    return render_to_response('problems_choose.html', { 'page_info' : page_info, 'problem_list' : problem_list } )


@contest_view
def add(request, page_info, id):
    
    problem = Problem(int(id))
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

            for ufile in glob.glob(os.path.join(fid, '*')):
                mapping.statement_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                mapping.statement = data['statement']
            except SphinxException as sphinxException:
                form._errors['statement'] = form.error_class([sphinxException])
                return render_to_response('problems_add.html', { 'fid' : fid,
                                                                 'form' : form, 
                                                                 'page_info' : page_info })
            return HttpResponseRedirect(reverse('contest_problems', args=[page_info.contest.id]))
        return render_to_response('problems_add.html', { 'form' : form, 
                                                         'page_info' : page_info,
                                                         'base' : problem })

    else:
        #TODO(kalq): Create a hash instead of full pathname
        fid = tempfile.mkdtemp()
        form = ProblemAddForm(suites=suites, initial={ 'fid' : fid })
        return render_to_response('problems_add.html', { 'page_info' : page_info,
                                                         'fid' : fid,
                                                         'form' : form,
                                                         'base' : problem } )
        
@contest_view
def edit(request, page_info, id):
    mapping = ProblemMapping(int(id))
    problem = mapping.problem
    suites = TestSuite.filter(TestSuiteStruct(problem=problem))
    pdf_file = mapping.statement_files_get("pdf")
    if request.method=="POST":
        form = ProblemAddForm(data=request.POST,files=request.FILES,suites=suites)
        if form.is_valid():
            data = form.cleaned_data
            fid = data['fid']
            if 'delete' in request.POST.keys():
                try:
                    mapping.delete()
                except:
                    return HttpResponseRedirect(reverse('contest_problems_edit', args=[page_info.contest.id,id]))                    
                return HttpResponseRedirect(reverse('contest_problems', args=[page_info.contest.id]))
            if 'remove_pdf' in request.POST.keys():
                mapping.statement_files_delete('pdf')
                return HttpResponseRedirect(reverse('contest_problems_edit', args=[page_info.contest.id,id]))                    
            for rfile in request.POST:
                if rfile.startswith('rfile'):
                    mapping.statement_files_delete(request.POST[rfile])
            for ufile in glob.glob(os.path.join(fid, '*')):
                mapping.statement_files_set_blob_path(os.path.basename(ufile), ufile)
            pdf = form.cleaned_data.get('pdf',None)
            if pdf:
                writer = Blob.create(pdf.size)
                writer.write(pdf.read())
                phash = writer.close()
                mapping.statement_files_set_blob_hash('pdf',phash)
        
            try:
            
                mapping.modify(ProblemMappingStruct(code=data['code'],
                                                    title=data['title'],
                                                    statement=data['statement'],
                                                    group=data['group'],
                                                    description=data['description'],
                                                    default_test_suite=TestSuite(int(data['suite']))))
            except SphinxException as sphinxException:
                attachments = valid_attachments(mapping.statement_files_get_list())
                form._errors['statement'] = form.error_class([sphinxException])
                return render_to_response('problems_add.html', { 'attachments' : attachments,
                                                                 'fid' : fid,
                                                                 'form' : form,
                                                                 'page_info' : page_info,
                                                                 'base' : problem,
                                                                 'editing' : mapping })
            if mapping.statement:
                return HttpResponseRedirect(reverse('contest_problems_view', args=[page_info.contest.id,id]))
            else:
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
                                                     'pdf_file' : pdf_file,
                                                     'editing' : mapping })

@contest_view
def view(request, page_info, id):
    problem = Web.get_problem_mapping_info(ProblemMapping(int(id)))
    content = fill_image_links(problem.html,'ProblemMapping',id, 'statement_files')
    return render_to_response('problems_view.html', {'page_info' : page_info, 'problemid' : id, 'content' : content })
    
