# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import RenderObjectButton
from satori.web.utils.tables import *
from satori.web.utils.rights import *
from satori.web.utils.generic_table import GenericTable
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django import forms


class PSetterAddForm(forms.Form):
    login = forms.CharField(required = True)

@general_view
def pagemove(request, page_info, id, direction):
    pass


@general_view
def view(request, page_info):

    subpages = GenericTable(prefix = 'subpages', request_get = request.GET)
    a = []
    for page in page_info.subpages:
        row = { 'id' : page.id, 'name' : page.name, 'order' : page.order, 'is_public' : page.is_public}
        row['visibility'] = 'admins'
        if logged_can_do(page):
            row['visibility'] = 'logged'
        if everyone_can_do(page):
            row['visibility'] = 'everyone'
        subpages.data.append(row)
    subpages.default_shown = 9999
    subpages.default_sortfield = 'order'
    subpages.autosort()
    subpages.autopaginate()
    
    
    class GlobalSubpages(ResultTable):
        def __init__(self,req,prefix):
            super(GlobalSubpages,self).__init__(req=req,prefix=prefix,autosort=False)
            self.results = [s for s in page_info.subpages]
            self.total = len(self.results)
#            self.fields.append(TableField(name='test',value=(lambda table,i : '0'),id=0))
            self.fields.append(TableField(name='',value=(lambda table,i : table.results[i].name),id=1))
            self.fields.append(TableField(name='',value=(lambda table,i : format_html('<a class="button button_small" href="{0}">Edit</a>', reverse('subpage_edit',args=[table.results[i].id]))),id=2))
            
    class PSetterTable(ResultTable):
        def __init__(self,req,prefix):
            super(PSetterTable,self).__init__(req=req,prefix=prefix,autosort=False)
            self.results = Privilege.global_list('MANAGE_PROBLEMS').keys()
            self.total = len(self.results)
            self.fields.append(TableField(name='',value=(lambda table,i : table.results[i].name),id=1))
            self.fields.append(TableField(name='',value='Revoke',render=(lambda table,i : RenderObjectButton(name='revoke',buttonname='Revoke',id=table.results[i].id,css='button button_small')),id=2))
            
    if request.method=='POST' and 'add' in request.POST.keys():
        form = PSetterAddForm(data=request.POST)
        if form.is_valid():
            try:
                user = User.filter(UserStruct(login=form.cleaned_data['login']))[0]
                Privilege.global_grant(user,'MANAGE_PROBLEMS')
                form = PSetterAddForm()
            except:
                form._errors["login"] = ['Privilege grant failed!']
    else:
        form = PSetterAddForm()
    if request.method=='POST' and 'revoke' in request.POST.keys():
        user_id = request.POST['id']
        user = User(int(user_id))
        Privilege.global_revoke(user,'MANAGE_PROBLEMS')
    is_priv_admin = Privilege.global_demand('MANAGE_PRIVILEGES')
    if is_priv_admin:
        problem_setters = PSetterTable(req=request.GET,prefix='psetters')
    else:
        problem_setters = None
    global_subpages = GlobalSubpages(req=request.GET,prefix='subpages')
    return render_to_response('configuration.html', {'page_info' : page_info, 'problem_setters' : problem_setters, 'form' : form, 'subpages' : subpages})
