# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')

def contest_view(func):
    def wrapped_contest_view(request, contestid, **kwargs):
        try:
            general_page_overview = Web.get_general_page_overview(Contest(contestid))
        except (TokenInvalid, TokenExpired):
            #redirect to login page 
            pass
        except ArgumentNotFound:
            #show error page to 404
            pass
        else:
            return func(request, general_page_overview, **kwargs)
    return wrapped_contest_view

def general_view(func):
    def wrapped_general_view(request, **kwargs):
        try:
            general_page_overview = Web.get_general_page_overview()
        except (TokenInvalid, TokenExpired):
            #redirect to login page 
            pass
        else:
            return func(request, general_page_overview, **kwargs)
    return wrapped_general_view
