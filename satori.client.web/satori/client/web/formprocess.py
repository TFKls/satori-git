from URLDictionary import *
from queries import *
from django.db import models
from satori.core.models import *


def LoginRequest(request):
    postvars = request.POST
    d = ParseURL(postvars['back_to'])
    try:
        m = User.objects.get(login__exact=request.POST['username'])
    except:
        d['login'][0]['status'] = ['failed']
    else:
        request.session['user'] = m.id

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

def SubmitRequest(request):
    d = ParseURL(request.POST['back_to'])
    d['content'] = [{'name' : ['results']}]
    p = ProblemMapping.objects.get(id = request.POST['problem'])
    c = Contestant.objects.get(id = request.POST['cid'])
    s = Submit(problem = p, owner = c, shortstatus = "Waiting")
    s.save()
    return GetLink(d,'')

def LogoutRequest(request):
    del Session.request.session['user']
    return GetLink(DefaultLayout(),'')

allreqs = {'login' : LoginRequest, 'logout' : LogoutRequest, 'join' : JoinContestRequest, 'accept' : AcceptUserRequest, 'submit' : SubmitRequest}

def process(argstr,request):
    return allreqs[argstr](request)
