
from URLDictionary import *
from satori.client.common import *

# Module for database queries


def UserById(uid):
	return User(int(uid))

def ContestById(cid):
	return Contest(int(cid))

def CurrentUser():
#        try:
        w = Security.whoami()
#        except:
#            return None
        return w

def ActiveContest(d):
	if not 'contestid' in d.keys():
		return None
	return ContestById(int(d['contestid'][0]))


def MyContestant(c):
    u = CurrentUser()
    if u and c:
	try:
	    cu = Contestant.filter(user = u, contest = c)[0]
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
	d = {'name' : ['cover'], 'cover' :[{'name' : ['main'], 'content' : [{'name' : ['news']} ], 'loginspace' : [{'name' : ['loginform']}]}]}
	#d = {'name' : ['main'], 'content' : [{'name' : ['news']} ], 'login' : [{'name' : ['login']}]}
	if a:
		d['contestid'] = [str(a.id)]
	return d
