# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response
from django import forms
from datetime import datetime
from satori.web.utils.datetimewidget import SatoriSplitDateTime

class ProblemsPublishForm(forms.Form):
    submitstart = forms.DateTimeField(required=False,widget=SatoriSplitDateTime, initial=datetime.now())
    submitfinish = forms.DateTimeField(required=False, widget=SatoriSplitDateTime, initial=datetime.now())
    def __init__(self,problem_list=[],data=None,*args,**kwargs):
        super(ProblemsPublishForm, self).__init__(data,*args, **kwargs)
        for pinfo in problem_list:
            if pinfo.is_admin:
                self.fields[str(pinfo.problem_mapping.id)] = forms.BooleanField(required=False)
    def clean(self):
        data = self.cleaned_data
        8/0
        


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
def view(request, page_info):
    problem_list = Web.get_problem_mapping_list(page_info.contest)
    if request.method=="POST":
        form = ProblemsPublishForm(data=request.POST,problem_list=problem_list)
        valid = form.is_valid()
        data = form.cleaned_data
        7/0
    form = ProblemsPublishForm(problem_list=problem_list)
    problems = []
    for pinfo in problem_list:
        p = {}
        p['select'] = form[str(pinfo.problem_mapping.id)]
        p['problem'] = pinfo.problem_mapping
        p['admin'] = pinfo.is_admin
        p['visible'] = between(pinfo.contestant_role_view_times,datetime.now())
        p['submittable'] = between(pinfo.contestant_role_submit_times,datetime.now())
        p['when_view'] = pinfo.contestant_role_view_times
        p['when_submit'] = pinfo.contestant_role_submit_times
        problems.append(p)
    return render_to_response('problems.html', { 'page_info' : page_info, 'form' : form, 'problems' : problems})
