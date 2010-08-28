# vim:ts=4:sts=4:sw=4:expandtab
from URLDictionary import *
from queries import *
from django.db import models
#from satori.core.models import *
from satori.client.common.remote import *
from django.http import HttpResponseRedirect
from django.http import HttpResponse

import urlparse
import urllib

class MetaRequest(type):
    allreqs = {}
    
    def __init__(cls, name, bases, attrs):
        super(MetaRequest, cls).__init__(name, bases, attrs)
        #We don't want abstract class here
        if name != "Request":
            if not hasattr(cls, 'pathName'):
                raise Exception('No pathName in request ' + name)
            if cls.pathName in MetaRequest.allreqs:
                raise Exception('Two requests with the same pathName!') 
            MetaRequest.allreqs[cls.pathName] = cls

class Request:
    __metaclass__ = MetaRequest
    def __init__(self,params,path):
        pass
    @classmethod
    def process(self, request):
        'To overload'
        raise Exception('Request.process not overloaded!')

class RegisterRequest(Request):
    pathName = 'register'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars.get('back_to', ''))
        path = vars['path']
        login = vars['username']
        password = vars['password']
        fullname = vars['fullname']
        Security.register(login=login, password=password, fullname=fullname)
        return GetLink(d, path)

class LoginRequest(Request):
    pathName = 'login'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars.get('back_to', ''))
        path = vars['path']
        lw_path = vars['lw_path']
        login = vars['username']
        password = vars['password']
        try:
            token_container.set_token(Security.login(login=login, password=password))
        except:
            pass
        return GetLink(d,path)

class OpenIdStartRequest(Request):
    pathName = 'openid_start'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars['back_to'])
        path = vars.get('path', '')
        lw_path = vars['lw_path']
        openid = vars['openid']
        finisher = request.build_absolute_uri()
        print finisher
        callback = urlparse.urlparse(finisher)
        qs = urlparse.parse_qs(callback.query)
        qs['back_to'] = (vars['back_to'],)
        qs['path'] = (vars['path'],)
        qs['lw_path'] = (vars['lw_path'],)
        query = []
        for key, vlist in qs.items():
            for value in vlist:
                query.append((key,value))
        query = urllib.urlencode(query)
        path = callback.path.split('.')
        path[-1] = 'openid_check'
        path = '.'.join(path)
        finisher = urlparse.urlunparse((callback.scheme, callback.netloc, path, callback.params, query, callback.fragment))
        print finisher
        try:
            res = Security.openid_login_start(openid=openid, return_to=finisher)
            token_container.set_token(res['token'])
            if res['html']:
                ret = HttpResponse()
                ret.write(res['html'])
                return ret;
            else:
                return HttpResponseRedirect(res['redirect'])
        except:
            follow(d,lw_path)['loginspace'][0]['status'] = ['failed']

class OpenIdCheckRequest(Request):
    pathName = 'openid_check'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        back_to = vars.get('back_to', '')
        path = vars.get('path', '')
        lw_path = vars.get('lw_path', '')
        d = ParseURL(back_to)
        print dict(request.REQUEST.items())
        try:
            token_container.set_token(Security.openid_login_finish(args=dict(request.REQUEST.items()), return_to=request.build_absolute_uri()))
        except:
            follow(d,lw_path)['loginspace'][0]['status'] = ['failed']
        return GetLink(d,path)

class OpenIdRegisterRequest(Request):
    pathName = 'openid_register'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars['back_to'])
        path = vars.get('path', '')
        lw_path = vars['lw_path']
        openid = vars['openid']
        login = vars['username']
        finisher = request.build_absolute_uri()
        print finisher
        callback = urlparse.urlparse(finisher)
        qs = urlparse.parse_qs(callback.query)
        qs['back_to'] = (vars['back_to'],)
        qs['path'] = (vars['path'],)
        qs['lw_path'] = (vars['lw_path'],)
        query = []
        for key, vlist in qs.items():
            for value in vlist:
                query.append((key,value))
        query = urllib.urlencode(query)
        path = callback.path.split('.')
        path[-1] = 'openid_confirm'
        path = '.'.join(path)
        finisher = urlparse.urlunparse((callback.scheme, callback.netloc, path, callback.params, query, callback.fragment))
        print finisher
        try:
            res = Security.openid_register_start(openid=openid, return_to=finisher, login=login)
            token_container.set_token(res['token'])
            if res['html']:
                ret = HttpResponse()
                ret.write(res['html'])
                return ret;
            else:
                return HttpResponseRedirect(res['redirect'])
        except:
            follow(d,lw_path)['loginspace'][0]['status'] = ['failed']

class OpenIdConfirmRequest(Request):
    pathName = 'openid_confirm'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        back_to = vars.get('back_to', '')
        path = vars.get('path', '')
        lw_path = vars.get('lw_path', '')
        d = ParseURL(back_to)
        print dict(request.REQUEST.items())
        try:
            token_container.set_token(Security.openid_register_finish(args=dict(request.REQUEST.items()), return_to=request.build_absolute_uri()))
        except:
            follow(d,lw_path)['loginspace'][0]['status'] = ['failed']
        return GetLink(d,path)

class LogoutRequest(Request):
    pathName = 'logout'
    @classmethod
    def process(cls, request):
        token_container.set_token('')
        return GetLink(DefaultLayout(),'')

class CreateContestRequest(Request):
    pathName = 'createcontest'
    @classmethod
    def process(cls, request):
        if request.POST['contestname']:
            Contest.create_contest(request.POST['contestname'])
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')

class JoinContestRequest(Request):
    pathName = 'join'
    @classmethod
    def process(cls, request):
        contest = ContestById(request.POST['contest_id'])
        contest.join_contest()
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')

class AcceptUserRequest(Request):
    pathName = 'accept'
    @classmethod
    def process(cls, request):
        cu = Contestant.filter({'id':int(request.POST['conuser_id'])})[0]
        contest = cu.contest
        contest.accept_contestant(cu)
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')

class ContestRightsRequest(Request):
    pathName = 'contestrights'
    @classmethod
    def process(cls, request):
        c = ContestById(request.POST['contest_id'])
        for rg in Privilege.filter({'object':c, 'role':Security.anonymous(), 'right':'VIEW'}):
            rg.delete()
        if 'anonymous_view' in request.POST.keys():
            Privilege.create({'object':c, 'role':Security.anonymous(), 'right':'VIEW'})
        for rg in Privilege.filter({'object':c, 'role':Security.authenticated()}):
            rg.delete()
        if request.POST['joining_by']=='moderated':
            Privilege.create({'object':c, 'role':Security.authenticated(), 'right':'APPLY'})
        if request.POST['joining_by']=='public':
            Privilege.create({'object':c, 'role':Security.authenticated(), 'right':'JOIN'})
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')

class AlterSuiteRequest(Request):
    pathName = 'altersuite'
    @classmethod
    def process(cls, request):
        pm = ProblemMapping.filter({'id':int(request.POST['pm_id'])})[0]
        dts = pm.default_test_suite
        nts = TestSuite.create({'problem ': pm.problem, 'dispatcher ': dts.dispatcher})
        for k in request.POST.keys():
            if k[0:4] == 'test':
                t = Test.filter({'id':int(k[4:])})[0]
                TestMapping.create({'test': t, 'suite': nts, 'order':t.id})
        pm.default_test_suite = nts
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')

class CreateProblemRequest(Request):
    pathName = 'createproblem'
    @classmethod
    def process(cls, request):
        p = Problem.create_problem(name=request.POST['name'])
        p.description = request.POST['description']
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
    
class SubmitRequest(Request):
    pathName = 'submit'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
        d['content'] = [{'name' : ['results']}]
        p = ProblemMapping(int(request.POST['problem']))
        c = Contestant(int(request.POST['cid']))
        s = Submit(problem = p, owner = c, shortstatus = "Waiting")
        return GetLink(d,'')

class EditMessageRequest(Request):
    pathName = 'editmsg'
    @classmethod
    def process(cls, request):
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

def process(argstr,request):
    res = MetaRequest.allreqs[argstr].process(request)
    if isinstance(res, HttpResponse):
    	return res
    return HttpResponseRedirect(res)
