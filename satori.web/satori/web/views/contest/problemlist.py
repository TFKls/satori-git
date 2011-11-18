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
from satori.web.utils.tables import ResultTable
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


class ProblemGroup(ResultTable):
    def __init__(self,req,prefix,table,name):
        super(ProblemGroup,self).__init__(req=req,prefix=prefix)
        self.results = table
        self.total = len(table)
        self.name = name
        self.fields.append(name='Code',value=lambda p : p.problem_mapping.code,id=1)
        self.fields.append(name='Code',value=lambda p : p.problem_mapping.title,id=2)
        
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
        if pinfo.problem_mapping.description and pinfo.problem_mapping.description!="":
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

