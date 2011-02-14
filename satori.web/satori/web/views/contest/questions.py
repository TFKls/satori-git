# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response

@general_view
def view(request, general_page_overview):
    return render_to_response('questions.html', general_page_overview)
