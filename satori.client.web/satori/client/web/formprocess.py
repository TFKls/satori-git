from URLDictionary import *
from queries import *
from django.db import models
from cdata.models import *

def LoginRequest(request):
	postvars = request.POST
	d = ParseURL(postvars['back_to'])
	try:
		m = User.objects.get(login__exact=request.POST['username'])
	except User.DoesNotExist:
		d['login'][0]['status'] = ['no_user']
	else:
		if m.password == request.POST['password']:
			request.session['user'] = m.id
			d['login'][0] = {'name' : ['login'] }
		else:
			d['login'][0]['status'] = ['failed']
	return GetLink(d,postvars['path'])

def JoinContestRequest(request):
	user_o = UserById(request.POST['user_id'])
	contest_o = ContestById(request.POST['contest_id'])
	cu = ConUser(user=user_o,contest=contest_o)
	if contest_o.joining==3:
		cu.accepted=True
	cu.save()
	d = DefaultLayout()
	d['content'] = [{'name' : ['selectcontest']}]
	return GetLink(d,'')

def AcceptUserRequest(request):
	cu = ConUser.objects.get(id = request.POST['conuser_id'])
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