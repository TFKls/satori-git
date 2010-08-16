# vim:ts=4:sts=4:sw=4:expandtab
from URLDictionary import *
from queries import *
from django.db import models
#from satori.core.models import *
from satori.client.common import *
from django.http import HttpResponseRedirect
from django.http import HttpResponse

def LoginRequest(request):
    postvars = request.POST
    d = ParseURL(postvars['back_to'])
    lw_path = postvars['lw_path']
    login = postvars['username']
    password = postvars['password']
    try:
        set_token(Security.login(login=login,password=password))
    except:
        follow(d,lw_path)['loginspace'][0]['status'] = ['failed']

    return GetLink(d,postvars['path'])

def OpenIdRequest(request):
    postvars = request.POST
    d = ParseURL(postvars['back_to'])
    lw_path = postvars['lw_path']
    openid = postvars['openid']
    finisher = GetLink(DefaultLayout(),'')
    try:
        res = Security.openid_start(openid=openid, realm='satori.tcs.uj.edu.pl', return_to=finisher)
        set_token(res['token'])
        if res['html']:
        	ret = HttpResponse()
        	ret.write(res['html'])
        	return ret;
        else:
            return HttpResponseRedirect(res['redirect'])
    except:
        raise
        follow(d,lw_path)['loginspace'][0]['status'] = ['failed']

def LogoutRequest(request):
    set_token('')
    return GetLink(DefaultLayout(),'')


def JoinContestRequest(request):
    user_o = UserById(request.POST['user_id'])
    contest_o = ContestById(request.POST['contest_id'])
    Contestant.filter(user=user_o,contest=contest_o)[0]
    if contest_o.joining=='Public':
        cu.accepted=True
    d = DefaultLayout()
    d['content'] = [{'name' : ['selectcontest']}]
    return GetLink(d,'')

def AcceptUserRequest(request):
    cu = Contestant(request.POST['conuser_id'])
    cu.accepted = True
    d = DefaultLayout()
    d['content'] = [{'name' : ['manusers']}]
    d['contestid'] = [str(cu.contest.id)]
    return GetLink(d,request.POST['back_path'])

def SubmitRequest(request):
    d = ParseURL(request.POST['back_to'])
    d['content'] = [{'name' : ['results']}]
    p = ProblemMapping(int(request.POST['problem']))
    c = Contestant(int(request.POST['cid']))
    s = Submit(problem = p, owner = c, shortstatus = "Waiting")
    return GetLink(d,'')

def EditMessageRequest(request):
    d = ParseURL(request.POST['back_to'])
    pv = request.POST
    if 'cancel' in pv.keys():
        return GetLink(d,'');
    if 'add' in pv.keys():
        if pv['msgtype']=='contest_only':
            c = Contest(pv['contest_id'])
            MessageContest(topic = pv['msgtopic'], contest = c, content = pv['msgcontent'])
        else:
            mso = (pv['msgtype']=='mainscreen_only')
            MessageGlobal(topic = pv['msgtopic'], content = pv['msgcontent'], mainscreenonly = mso)
        return GetLink(d,'')
    m = None
    try:
        m = MessageGlobal(pv['msgid'])
    except:
        m = MessageContest(pv['msgid'])
    if 'edit' in pv.keys():
        m.topic = pv['msgtopic']
        m.content = pv['msgcontent']
        m.save()
        return GetLink(d,'')
    if 'delete' in pv.keys():
        m.delete()
        return GetLink(d,'')


allreqs = {'login' : LoginRequest, 'openid' : OpenIdRequest, 'logout' : LogoutRequest, 'join' : JoinContestRequest, 'accept' : AcceptUserRequest, 'submit' : SubmitRequest, 'editmsg' : EditMessageRequest}

def process(argstr,request):
    res = allreqs[argstr](request)
    if isinstance(res, HttpResponse):
    	return res
    return HttpResponseRedirect(res)
