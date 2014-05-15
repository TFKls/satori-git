# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django import forms
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from satori.web.utils.generic_table import GenericTable
import datetime

@contest_view
def view(request, page_info):
    contest = page_info.contest
    contestant = page_info.contestant
    is_admin = page_info.contest_is_admin
    class BackupForm(forms.Form):
        name = forms.CharField(label='Name',initial=unicode(datetime.datetime.now()),required=True)
        codefile = forms.FileField(label='Upload file',required=True)
    
    backups = GenericTable('backups',request.GET)
    if is_admin:
        clist = Contestant.filter(ContestantStruct(contest=contest))
    else:
        clist = [contestant]
    for contestant in clist:
        for backup in contestant.backup_get_list():
            backups.data.append({'contestant_id' : contestant.id, 'contestant_name' : contestant.name, 'backup_name' : backup.name, 'backup_filename' : backup.filename})
    backups.default_shown=30
    backups.default_sortfield='backup_name'
    backups.autosort()
    backups.autopaginate()
    if request.method == "POST":
        if 'delete' in request.POST.keys():
            c = Contestant(int(request.POST["cid"]))
            c.backup_delete(request.POST["id"])
            return HttpResponseRedirect(reverse('backup',args=[page_info.contest.id]))
        if 'clearall' in request.POST.keys() and is_admin:
            for c in Contestant.filter(ContestantStruct(contest=contest)):
                for oa in c.backup_get_list():
                    c.backup_delete(oa.name)
            return HttpResponseRedirect(reverse('backup',args=[page_info.contest.id]))
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
    return render_to_response('backup.html', {'page_info' : page_info, 'backups' : backups, 'add_form' : form})
        

def placeholder(request,page_info):
    class BackupTable(ResultTable):
        def default_limit(self):
            return 20
        def __init__(self,req,prefix=''):
            super(BackupTable,self).__init__(req=req,prefix=prefix,default_sort=2,default_desc=True)
            self.results = []
            self.contestants = []
            self.total = len(self.results)
            if is_admin:
                self.fields.append(TableField(name='Contestant',value=(lambda table,i : table.contestants[i].name),id=1))
            self.fields.append(TableField(name='Name',value=(lambda table,i : table.results[i].name),id=2))
            def download_link(table,i):
                name=table.results[i].name
                filename=table.results[i].filename
                url = reverse('download_group',args=['download','Contestant',str(table.contestants[i].id),'backup',name,filename])
                return format_html(u'<a href="{0}" class="stdlink">{1}</a>', url, filename)
            self.fields.append(TableField(name='File',value=(lambda table,i : table.results[i].filename),render=download_link,id=3,sortable=False))
            def delete_form(table,i):
                return format_html(u'<form action="" method="POST"><input type="hidden" name="id" value="{0}"/><input type="hidden" name="cid" value="{1}"/><input class="button button_small"' +
                                    ' type="submit" name="delete" value="Delete"></form>', table.results[i].name, table.contestants[i].id)
            self.fields.append(TableField(name='',value='',render=delete_form,id=4,sortable=False,css=['centered']))
            
    backups = BackupTable(req=request.GET,prefix='backup')
    return render_to_response('backup.html', {'page_info' : page_info, 'form' : form, 'backups' : backups})

