from satori.core.models import *
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from URLDictionary import *
from widget import *
from formprocess import *
				
def load(request,argstr,path = ""):
	Session.request = request
	Session.vars = request.session
	params = ParseURL(argstr)
	w = Widget.FromDictionary(params,path)
	return render_to_response(w.htmlFile, {'widget' : w} )

def loadPOST(request,argstr=""):
	Session.request = request
	Session.vars = request.session
	redir = process(argstr,request)
	return HttpResponseRedirect(redir)
