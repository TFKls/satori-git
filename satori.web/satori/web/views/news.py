# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response

@general_view
def view(request, general_page_overview):
    messages = Subpage.get_global(True)
    html_messages = []
    for m in messages:
        html_messages.append({'m' : m, 'content' : text2html(m.content)})
    html_messages.sort(key=lambda msg: msg['m'].date_created, reverse=True)
    return render_to_response('news.html', {'general_page_overview' : general_page_overview, 'html_messages' : html_messages})
