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
    return render_to_response('print.html', {'page_info' : page_info, 'form' : form})

