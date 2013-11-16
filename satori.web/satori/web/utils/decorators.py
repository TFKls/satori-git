# vim:ts=4:sts=4:sw=4:expandtab
import traceback
import sys
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from django.shortcuts import render_to_response
from satori.client.common import want_import
from django.views.debug import ExceptionReporter
from thrift.transport.TTransport import TTransportException
want_import(globals(), '*')

def contest_view(func):
    def wrapped_contest_view(request, contestid=None, **kwargs):
        try:
            token_container.set_token(request.COOKIES.get(settings.SATORI_TOKEN_COOKIE_NAME, ''))
        except:
            token_container.set_token('')
        page_info = None
        try:
            if contestid is not None:
                try:
                    page_info = Web.get_page_info(Contest(int(contestid)))
                except:
                    page_info = Web.get_page_info()
                    raise
            else:
                page_info = Web.get_page_info()
            page_info.url = urlquote(request.path)
            res = func(request, page_info, **kwargs)
            if request.COOKIES.get(settings.SATORI_TOKEN_COOKIE_NAME, '') != token_container.get_token():
                res.set_cookie(settings.SATORI_TOKEN_COOKIE_NAME,
                        token_container.get_token(),
                        domain=settings.SATORI_TOKEN_COOKIE_DOMAIN,
                        path=settings.SATORI_TOKEN_COOKIE_PATH,
                        secure=settings.SATORI_TOKEN_COOKIE_SECURE or None,
                        httponly=settings.SATORI_TOKEN_COOKIE_HTTPONLY or None)
            return res
        except (TokenInvalid, TokenExpired):
            res = HttpResponseRedirect(reverse('login')+'?redir='+urlquote(request.path))
            res.set_cookie(settings.SATORI_TOKEN_COOKIE_NAME, '')
            return res
        except AccessDenied:
            if page_info and not page_info.role:
                return HttpResponseRedirect(reverse('login')+'?redir='+urlquote(request.path))
            if request.method == 'POST':
                info = 'You don\'t have rights to perform the requested action.'
            else:
                info = 'You don\'t have rights to view the requested object.'
            res = render_to_response('error.html', { 'page_info' : page_info, 'message': 'Access denied', 'info': info })
            res.status_code = 403
            return res
        except ArgumentNotFound:
            res = render_to_response('error.html', { 'page_info' : page_info, 'message': 'Object not found', 'info': 'The requested object does not exist.' })
            res.status_code = 404
            return res
        except TTransportException:
            res = render_to_response('error.html', { 'page_info' : page_info, 'message': 'Server error', 'info': 'Communication with the core server failed.' })
            res.status_code = 500
            return res
        except Exception as e:
            traceback.print_exc()
            if settings.DEBUG:
                reporter = ExceptionReporter(request, *sys.exc_info())
                detail = reporter.get_traceback_html()
                detail2 = []
                in_style = False
                for line in detail.split('\n'):
                    if line.startswith('  </style'):
                        in_style = False
                    if line == '    #summary { background: #ffc; }':
                        line = '    #summary { background: #eee; }'
                    if in_style:
                        line = '  #content ' + line
                    if line.startswith('  <style'):
                        in_style = True
                    detail2.append(line)
                detail = '\n'.join(detail2)
            else:
                detail = ''
            res = render_to_response('error.html', { 'page_info' : page_info, 'message': 'Internal server error', 'info': 'The server encountered an internal error.', 'detail': detail })
            res.status_code = 500
            return res
    return wrapped_contest_view

general_view = contest_view
