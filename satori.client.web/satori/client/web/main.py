from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from satori.client.common import want_import
want_import(globals(), '*')
from URLDictionary import *
from satori.client.web.widgets import Widget
from requests import process
from getfile import *
from queries import DefaultLayout
from base64 import *
import re
                
def load(request,argstr):
#    try:
	Session.request = request
	try:
            token_container.set_token(request.COOKIES.get('satori_token', ''))
        except:
            token_container.set_token('')
        args = re.split('\.',unmask(argstr))
	params = ParseURL(args[0])
	if len(args)>=2:
            path = args[1]
        else:
            path = ''
	try:
            w = Widget.FromDictionary(params,path)
            res = render_to_response(w.htmlFile, {'widget' : w} )
        except (TokenInvalid, TokenExpired):
            token_container.set_token('')
	    link = GetLink(DefaultLayout(dict=params,maincontent='loginform'),path)
	    res = HttpResponseRedirect(link)
	    res.set_cookie('satori_token', '')
	    return res
	if request.COOKIES.get('satori_token', '') != token_container.get_token():
	    res.set_cookie('satori_token', token_container.get_token())
	return res
#    except Exception as e:
#        raise e
        return render_to_response('htmls/error.html')
        
def activate(request,argstr):
    try:
	Session.request = request
        try:
            token_container.set_token(request.COOKIES.get('satori_token', ''))
        except:
            token_container.set_token('')
        try:
            User.activate(argstr)
            link = GetLink(DefaultLayout(maincontent='loginform',status=['activated']),'')
            res = HttpResponseRedirect(link)
            return res
        except(TokenInvalid):
            User.activate(argstr)
            link = GetLink(DefaultLayout(maincontent='loginform'),'')
            res = HttpResponseRedirect(link)
            return res
        except:
            link = GetLink(DefaultLayout(maincontent='loginform',status=['activation_failed']),'')
            res = HttpResponseRedirect(link)        
            return res
    except Exception as e:
        return render_to_response('htmls/error.html')


def loadPOST(request,argstr=""):
    try:
	Session.request = request
        try:
            token_container.set_token(request.COOKIES.get('satori_token', ''))
        except:
            token_container.set_token('')
        try:
            res = process(argstr,request)
        except (TokenInvalid, TokenExpired):
            link = GetLink(DefaultLayout(dict=params,maincontent='loginform'),'')
            res = HttpResponseRedirect(link)
            res.set_cookie('satori_token', '')
            return res
	if request.COOKIES.get('satori_token', '') != token_container.get_token():
	    res.set_cookie('satori_token', token_container.get_token())
	return res
    except Exception as e:
        raise e
        return render_to_response('htmls/error.html')

def loadfile(request,argstr=""):
    try:
	Session.request = request
	try:
            token_container.set_token(request.COOKIES.get('satori_token', ''))
        except:
            token_container.set_token('')
        try:
            res = getfile(argstr,request)
        except (TokenInvalid, TokenExpired):
            link = GetLink(DefaultLayout(dict=params,maincontent='loginform'),'')
            res = HttpResponseRedirect(link)
            res.set_cookie('satori_token', '')
            return res
	if request.COOKIES.get('satori_token', '') != token_container.get_token():
	    res.set_cookie('satori_token', token_container.get_token())
	return res
    except Exception as e:
        raise e
        return render_to_response('htmls/error.html')
