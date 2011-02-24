# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response

@contest_view
def view(request, page_info):
    return render_to_response('print.html', {'page_info' : page_info})
