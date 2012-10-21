# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django import forms
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from satori.web.utils.tables import *

@contest_view
def view(request, page_info):
    contest = page_info.contest
    contestant = page_info.contestant
    is_admin = page_info.contest_is_admin
    class PrintForm(forms.Form):
        codefile = forms.FileField(label='Print file',required=True)

    class PrintTable(ResultTable):
        def default_limit(self):
            return 20
        def __init__(self,req,prefix=''):
            super(PrintTable,self).__init__(req=req,prefix=prefix,default_sort=2,default_desc=True)
            self.results = PrintJob.filter(PrintJobStruct(contest=contest))
            self.total = len(self.results)
            if is_admin:
                self.fields.append(TableField(name='Contestant',value=(lambda table,i : table.results[i].contestant.name),id=1))
            self.fields.append(TableField(name='Time',value=(lambda table,i : table.results[i].time),id=2))
            self.fields.append(TableField(name='Status',value=(lambda table,i : table.results[i].status),id=3))
            self.fields.append(TableField(name='Report',value=(lambda table,i : table.results[i].report),id=4))

        
    if request.method == "POST":
        form = PrintForm(request.POST,request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            if data["codefile"]:
                if data["codefile"].size>100000:
                    raise Exception('File too large for print.')
                content = data["codefile"].read()
                filename = data["codefile"].name
                #HACK: check if blob not too large
                PrintJob.create(PrintJobStruct(contest=contest),content=content,filename=filename)
            return HttpResponseRedirect(reverse('print',args=[page_info.contest.id]))
    else:
        form = PrintForm()
    prints = PrintTable(req=request.GET,prefix='print')
    return render_to_response('print.html', {'page_info' : page_info, 'form' : form, 'prints' : prints})

        