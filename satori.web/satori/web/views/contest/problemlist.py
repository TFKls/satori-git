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
from django.utils.html import mark_safe
from django import forms
from datetime import datetime
from satori.web.utils.files import valid_attachments
from satori.web.utils.generic_table import GenericTable
from satori.web.utils.shortcuts import text2html,fill_image_links

class ProblemsPublishForm(forms.Form):
#    submitstart = SatoriDateTimeField(required=False)
#    submitfinish = SatoriDateTimeField(required=False)
    group = forms.CharField(required=False)
#    viewauto = forms.BooleanField(required=False,initial=True)
#    viewstart = SatoriDateTimeField(required=False)
#    viewfinish = SatoriDateTimeField(required=False)
        
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
def viewall(request,page_info):
    contest = page_info.contest
    problems = GenericTable('problems',request.GET)
    problem_list = Web.get_problem_mapping_list(page_info.contest)
    for problem in problem_list:
        m = problem.problem_mapping
        problems.data.append({'code' : m.code, 'title' : m.title, 'id' : m.id})
    return render_to_response('problemlist.html', {'page_info' : page_info, 'problems' : problems})

        
@contest_view
def placeholder(request,page_info):
    class ProblemsTable(ResultTable):
        @staticmethod
        def default_limit():
            return 0
        def __init__(self,req,problem_list,group,admin):
            self.groupname = group
            prefix = 'p'+unicode(hash(group))
            super(ProblemsTable,self).__init__(req=req,prefix=prefix,autosort=True)
            if not self.params.get('sort',None):
                self.params['sort']='code'
                self.params['order']='asc'
            self.results = [p for p in problem_list if p.problem_mapping.group==group]
            def view_link(table,i):
                p = table.results[i]
                if not p.problem_mapping.statement:
                    return p.problem_mapping.title
                else:
                    return format_html(u'<a class="stdlink" href="{0}">{1}</a>', reverse('contest_problems_view',args=[unicode(page_info.contest.id),unicode(p.problem_mapping.id)]), p.problem_mapping.title)
            def visible(table,i):
                p = table.results[i]
                if between(p.contestant_role_view_times,datetime.now()):
                    return mark_safe('<div class="highlight_pos"><span class="tinytext">Visible</span></div>')
                else:
                    return mark_safe('<div class="highlight_neg"><span class="tinytext">Invisible</span></div>')
            def submittable(table,i):
                p = table.results[i]
                v = p.contestant_role_submit_times
                active = between(v,datetime.now())
                s = ""
                if active:
                    s+='<div class="highlight_pos"><span class="tinytext">'
                else:
                    s+='<div class="highlight_neg"><span class="tinytext">'
                if active:
                    s+='Submitting enabled'
                    if v and v.start_on:
                        s += ', started at '+str(v.start_on)
                elif v and v.start_on:
                    s += 'Submiting starts at '+str(v.start_on)
                if v and v.finish_on:
                    if not v or not v.start_on:
                        s += 'Submitting '
                    else:
                        s += ', '
                    s += 'ends on '+str(v.finish_on)
                if not v:
                    s += 'Submitting disabled'
                s += "</span></div>"
                # FIXME(robryk): Make this saner
                return mark_safe(s)
            def edit_button(table,i):
                p = table.results[i]
                if p.is_admin:
                    return format_html(u'<a class="button button_small" href="{0}">Edit</a>', reverse('contest_problems_edit',args=[unicode(page_info.contest.id),unicode(table.results[i].problem_mapping.id)]))
                else:
                    return ''
            def submit_button(table,i):
                p = table.results[i]
                if p.can_submit:
                    return format_html(u'<a class="button button_small" href="{0}?select={1}">Submit</a>', reverse('submit',args=[unicode(page_info.contest.id)]), table.results[i].problem_mapping.id)
                else:
                    return ''
            def pdflink(table,i):
                p = table.results[i]
                url = reverse('download_group',args=['view','ProblemMapping',str(p.problem_mapping.id),'statement_files','_pdf',p.problem_mapping.code+'.pdf'])
                return format_html(u'<a class="button button_small" href="{0}">PDF</a>', url) if p.has_pdf else ''
            if admin:
                self.fields.append(TableField(name='',value='',render=lambda table,i: format_html(u'<input type="checkbox" class="check" name="pm_{0}">', table.results[i].problem_mapping.id) if table.results[i].is_admin else '',id='box',sortable=False,css=['centered','small']))
            self.fields.append(TableField(name='Code',value=(lambda table,i: table.results[i].problem_mapping.code),id='code',css=['centered','small']))
            self.fields.append(TableField(name='Title',value=(lambda table,i: table.results[i].problem_mapping.title),
                                                       render=view_link,id='title'))
            self.fields.append(TableField(name='PDF',value='',render=pdflink,id='pdf',sortable=False,css=['centered','small']))
            self.fields.append(TableField(name='',value=(lambda table,i: table.results[i].problem_mapping.description),
                                                  render=(lambda table,i: mark_safe(text2html(table.results[i].problem_mapping.description)) if table.results[i].problem_mapping.description else ''),
                                                  id='desc'))
            if admin:
                self.fields.append(TableField(name='',value='',render=visible,id='visibility',sortable=False,css=['small','centered']))
                self.fields.append(TableField(name='',value='',render=submittable,id='submits',sortable=False,css=['medium']))
            if admin:
                self.fields.append(TableField(name='',value='',render=edit_button,id='edit',sortable=False,css=['centered','small']))
            self.fields.append(TableField(name='',value='',render=submit_button,id='submit',sortable=False,css=['centered','small']))
            self.total = len(self.results)

    problem_list = Web.get_problem_mapping_list(page_info.contest)
    
    if request.method=="POST":
        form = ProblemsPublishForm(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            selected = []
            role = page_info.contest.contestant_role
            for pinfo in problem_list:
                id = str(pinfo.problem_mapping.id)
                if 'pm_'+str(id) in request.POST.keys():
                    selected.append(pinfo.problem_mapping)
            if "changesubmit" in request.POST.keys():
                for s in selected:
                    start = data.get('submitstart',None)
                    finish = data.get('submitfinish',None)
                    Privilege.grant(role,s,'SUBMIT',PrivilegeTimes(start_on=start,finish_on=finish))
                    Privilege.grant(role,s,'VIEW',PrivilegeTimes(start_on=start))
#            elif "changeview" in request.POST.keys():
#                for s in selected:
#                    start = data.get('viewstart',None)
#                    finish = data.get('viewfinish',None)
#                    Privilege.grant(role,s,'VIEW',PrivilegeTimes(start_on=start,finish_on=finish))
            elif "revokesubmit" in request.POST.keys():
                for s in selected:
                    Privilege.revoke(role,s,"SUBMIT")
            elif "revokeview" in request.POST.keys():
                for s in selected:
                    Privilege.revoke(role,s,"SUBMIT")
                    Privilege.revoke(role,s,"VIEW")
            elif "publish" in request.POST.keys():
                for s in selected:
                    Privilege.grant(role,s,"VIEW")
            elif "addgroup" in request.POST.keys():
                for s in selected:
                    s.group = data.get('group','')
            return HttpResponseRedirect(reverse('contest_problems',args=[page_info.contest.id]))
    form = ProblemsPublishForm()
    any_admin = False
    groupnames = []
    for p in problem_list:
        if p.is_admin:
            any_admin = True
        if not p.problem_mapping.group in groupnames:
            groupnames.append(p.problem_mapping.group)
    groupnames.sort()
    groups = []
    for g in groupnames:
        groups.append(ProblemsTable(req=request.GET,problem_list=problem_list,group=g,admin=any_admin))
    return render_to_response('problems.html', { 'page_info' : page_info, 'groups' : groups, 'form' : form, 'admin' : any_admin, 'moregroups' : len(groupnames)>1 or (len(groupnames)==1 and groupnames[0])})
    
