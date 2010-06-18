
from URLDictionary import *
from satori.core.models import *

# Module for database queries


def UserById(uid):
	return User.objects.get(id=uid)

def ContestById(cid):
	return Contest.objects.get(id=cid)

def CurrentUser():
	if not ('user' in Session.request.session.keys()):
		return None
	else:
		u = Session.request.session['user']
		return UserById(u)

def ActiveContest(d):
	if not 'contestid' in d.keys():
		return None
	return ContestById(d['contestid'][0])


def MyContestant(c)
    u = CurrentUser()
    if u and c:
	try:
	    cu = Contestant.objects.get(user = u.id, contest = c.id)
	except:
	    return None
	else:
	    return cu
    else:
	return None
    
def CurrentContestant(d):
	return MyContestant(ActiveContest(d))

def Allowed(o, str):
	return True

# default dictionary, if need to return to main screen
def DefaultLayout(dict = {}):
	a = ActiveContest(dict)
	d = {'name' : ['main'], 'content' : [{'name' : ['news']} ], 'login' : [{'name' : ['login']}]}
	if a:
		d['contestid'] = [str(a.id)]
	return d
