# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import StatusBar
from satori.web.utils.tables import *
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

class EditUserForm(forms.Form):
    login = forms.CharField(required=True,label='User login:')

@general_view
def view(request, page_info):
    if request.method=='POST':
        form = EditUserForm(request.POST)
        bar = StatusBar()
        if form.is_valid():
            try:
                user = User.filter(UserStruct(login=form.cleaned_data['login']))[0]
                return HttpResponseRedirect(reverse('profile',args=[user.id]))
            except:
                bar.errors.append('Cannot edit user.')
    form = EditUserForm()
    
    class UserTable(ResultTable):
    
        def __init__(self,req,prefix=''):
            super(UserTable,self).__init__(req=req,prefix=prefix)
            self.results = User.filter(UserStruct())
            self.total = len(self.results)
            
            self.fields.append(TableField(name='Login',value=(lambda table,i: table.results[i].login), 
                                          render = lambda table,i: '<a class="stdlink" href="'+str(reverse('profile',args=[table.results[i].id]))+'">'+table.results[i].login+'</a>',
                                          id=1 ))
            self.fields.append(TableField(name='First name',value=(lambda table,i: table.results[i].firstname), id=2 ))
            self.fields.append(TableField(name='Last name',value=(lambda table,i: table.results[i].lastname), id=3 ))
            self.fields.append(TableField(name='E-mail',value=(lambda table,i: str(table.results[i].email)), id=4 ))
            affiliation = TableField(name='Affiliation',value=(lambda table,i: str(table.results[i].profile_get_str('affiliation'))), id=5)
            self.fields.append(affiliation)
            self.add_autofilter(affiliation)
        
    user_list = UserTable(req=request.GET,prefix='users')
    return render_to_response('users.html', {'page_info' : page_info, 'edit_form' : form, 'user_list' : user_list})
