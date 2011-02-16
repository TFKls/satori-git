# vim:ts=4:sts=4:sw=4:expandtab

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from satori.client.common import want_import
want_import(globals(), '*')

def contest_view(func):
    def wrapped_contest_view(request, contestid, **kwargs):
        try:
            token_container.set_token(request.COOKIES.get('satori_token', ''))
        except:
            token_container.set_token('')
        try:
            general_page_overview = Web.get_general_page_overview(Contest(int(contestid)))
        except (TokenInvalid, TokenExpired):
            token_container.set_token('')
            res = HttpResponseRedirect(reverse('login'))
        except ArgumentNotFound:
            #show error page to 404
            pass
        else:
            res = func(request, general_page_overview, **kwargs)
        if request.COOKIES.get('satori_token', '') != token_container.get_token():
            res.set_cookie('satori_token', token_container.get_token())
        return res
    return wrapped_contest_view

def general_view(func):
    def wrapped_general_view(request, **kwargs):
        try:
            token_container.set_token(request.COOKIES.get('satori_token', ''))
        except:
            token_container.set_token('')
        try:
            general_page_overview = Web.get_general_page_overview()
        except (TokenInvalid, TokenExpired):
            token_container.set_token('')
            res = HttpResponseRedirect(reverse('login'))
        else:
            res = func(request, general_page_overview, **kwargs)
        if request.COOKIES.get('satori_token', '') != token_container.get_token():
            res.set_cookie('satori_token', token_container.get_token())
        return res
    return wrapped_general_view
