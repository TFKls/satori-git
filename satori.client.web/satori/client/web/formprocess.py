from URLDictionary import *
from queries import *
from django.db import models
from satori.core.models import *

def LoginRequest(request):
	request.session['user'] = m.id
	d['login'][0] = {'name' : ['login'] }
	return GetLink(d,postvars['path'])

def JoinContestRequest(request):
	user_o = UserById(request.POST['user_id'])
	contest_o = ContestById(request.POST['contest_id'])
	cu = Contestant(user=user_o,contest=contest_o)
	if contest_o.joining=='Public':
		cu.accepted=True
	cu.save()
	d = DefaultLayout()
	d['content'] = [{'name' : ['selectcontest']}]
	return GetLink(d,'')

def AcceptUserRequest(request):
	cu = Contestant.objects.get(id = request.POST['conuser_id'])
	cu.accepted = True
	cu.save()
	d = DefaultLayout()
	d['content'] = [{'name' : ['manusers']}]
	d['contestid'] = [str(cu.contest.id)]
	return GetLink(d,request.POST['back_path'])

def LogoutRequest(request):
	del Session.request.session['user']
	return GetLink(DefaultLayout(),'')

allreqs = { 'login' : LoginRequest, 'logout' : LogoutRequest, 'join' : JoinContestRequest, 'accept' : AcceptUserRequest}

def process(argstr,request):
	return allreqs[argstr](request)