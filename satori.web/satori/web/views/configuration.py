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



@general_view
def pagemove(request, page_info, id, direction):
    page_info.subpages.sort(key=lambda page : page.order)
    page = Subpage(int(id))
    if page in page_info.subpages:
        i = page_info.subpages.index(page)
        if i>=0 and direction=='up':
            page_info.subpages[i],page_info.subpages[i-1] = page_info.subpages[i-1],page_info.subpages[i]
        if i<len(page_info.subpages)-1 and direction=='down':
            page_info.subpages[i],page_info.subpages[i+1] = page_info.subpages[i+1],page_info.subpages[i]
    for i in range(0, len(page_info.subpages)):
        page_info.subpages[i].modify(SubpageStruct(order=i+1))
    return HttpResponseRedirect(reverse('configuration'))

@general_view
def pagedelete(request, page_info):
    try:
        id = request.POST['id']
        subpage = Subpage(int(id))
        subpage.delete()
        return HttpResponseRedirect(reverse('configuration'))
    except:
        return HttpResponseRedirect(reverse('configuration')+'?status=page_del_failed')

@general_view
def problemsetter_grant(request, page_info):
    try:
        login = request.POST['login']
        user = User.filter(UserStruct(login=login))[0]
        Privilege.global_grant(user,'MANAGE_PROBLEMS')
        return HttpResponseRedirect(reverse('configuration'))
    except:
        return HttpResponseRedirect(reverse('configuration')+'?status=user_grant_failed')


@general_view
def problemsetter_revoke(request, page_info):
    try:
        id = request.POST['id']
        user = User(int(id))
        Privilege.global_revoke(user,'MANAGE_PROBLEMS')
        return HttpResponseRedirect(reverse('configuration'))
    except:
        return HttpResponseRedirect(reverse('configuration')+'?status=user_revoke_failed')


@general_view
def view(request, page_info):

    subpages = GenericTable(prefix = 'subpages', request_get = request.GET)
    for page in page_info.subpages:
        row = { 'id' : page.id, 'name' : page.name, 'order' : page.order, 'is_public' : page.is_public}
        row['visibility'] = 'admins'
        if logged_can_do(page):
            row['visibility'] = 'logged'
        if everyone_can_do(page):
            row['visibility'] = 'everyone'
        subpages.data.append(row)
    subpages.default_sortfield = 'order'
    subpages.autosort()
    subpages.autopaginate()
    
    problemsetters = GenericTable(prefix = 'problemsetters', request_get = request.GET)        
    for role in Privilege.global_list('MANAGE_PROBLEMS').keys():
        row = {'name' : role.name, 'id' : role.id}
        try:
            row['login'] = User(role.id).login        
        except:
            row['login'] = ''
        problemsetters.data.append(row)
    problemsetters.default_sortfield = 'login'
    problemsetters.autosort()
    problemsetters.autopaginate()
    
    return render_to_response('configuration.html', {'page_info' : page_info, 'problemsetters' : problemsetters, 'subpages' : subpages})
