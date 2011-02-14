# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response

@contest_view
def view(request, general_page_overview,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    name = subpage.name
    content = subpage.content
    return render_to_response('contestsubpage.html',{'name' : name, 'content' : content})
