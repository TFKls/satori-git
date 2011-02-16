# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

@general_view
def view(request, page_info):
    if token_container.get_token()!='':
        token_container.set_token('')
        return HttpResponseRedirect(reverse('logout'))
    else:
        return render_to_response('logout.html', {'page_info' : page_info})
