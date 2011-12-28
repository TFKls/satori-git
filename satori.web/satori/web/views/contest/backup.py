# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django import forms
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from satori.web.utils.tables import *
import datetime

@contest_view
def view(request, page_info):
    contest = page_info.contest
    contestant = page_info.contestant
    class BackupForm(forms.Form):
        name = forms.CharField(label='Name',initial=unicode(datetime.datetime.now()),required=True)
        codefile = forms.FileField(label='Upload file',required=True)
        
#        def clean(self):
#            data = self.cleaned_data
#            if data["code"]=="" and not data["codefile"]:
#            if not data["codefile"]:
#                raise forms.ValidationError("No code given!")
#            return data
    class BackupTable(ResultTable):
        def default_limit(self):
            return 20
        def __init__(self,req,prefix=''):
            super(BackupTable,self).__init__(req=req,prefix=prefix)
            self.results = contestant.backup_get_list()
            self.total = len(self.results)
            self.fields.append(TableField(name='Name',value=(lambda table,i : table.results[i].name),id=1))
            def download_link(table,i):
                name=table.results[i].name
                filename=table.results[i].filename
                url = reverse('download_group',args=['download','Contestant',str(contestant.id),'backup',name,filename])
                return '<a href="'+url+'" class="stdlink">'+filename+'</a>'
            self.fields.append(TableField(name='File',value=(lambda table,i : table.results[i].filename),render=download_link,id=2))
            
    if request.method == "POST":
        form = BackupForm(request.POST,request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            if data["codefile"]:
                content = data["codefile"]
                filename = content.name
                #HACK: check if blob not too large
                if content.size>100000:
                    raise Exception('File too large for backup.')
                writer = contestant.backup_set_blob(data['name'],content.size,filename)
                writer.write(content.read())
                writer.close()

            return HttpResponseRedirect(reverse('backup',args=[page_info.contest.id]))
    else:
        form = BackupForm()
    backups = BackupTable(req=request.GET,prefix='backup')
    return render_to_response('backup.html', {'page_info' : page_info, 'form' : form, 'backups' : backups})
