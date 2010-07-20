from satori.core.models import *
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from URLDictionary import *
from widget import *
from formprocess import *
                
def load(request,argstr,path = ""):
	Session.request = request
	Session.user = request.COOKIES.get('satori_user', None)
	params = ParseURL(argstr)
	w = Widget.FromDictionary(params,path)
	res = render_to_response(w.htmlFile, {'widget' : w} )
	if request.COOKIES.get('satori_user', None) != Session.user:
	    res.set_cookie('satori_user', Session.user)
	return res

def loadPOST(request,argstr=""):
	Session.request = request
	Session.user = request.COOKIES.get('satori_user', None)
	redir = process(argstr,request)
	res = HttpResponseRedirect(redir)
	if request.COOKIES.get('satori_user', None) != Session.user:
	    res.set_cookie('satori_user', Session.user)
	return res
