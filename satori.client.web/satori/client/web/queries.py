
from URLDictionary import *
from satori.client.common import *

# Module for database queries


def UserById(uid):
	return User(int(uid))

def ContestById(cid):
	return Contest(int(cid))

def CurrentUser():
  try:
    return Security.whoami()
  except:
    return None

def ActiveContest(d):
	if not 'contestid' in d.keys():
		return None
	return ContestById(int(d['contestid'][0]))


def MyContestant(c):
    u = CurrentUser()
    if u and c:
	try:
	    cu =c.find_contestant(user = u)
	except:
	    return None
	else:
	    return cu
    else:
	return None
	

def CurrentContestant(d):
	return MyContestant(ActiveContest(d))

def Allowed(o, str):
    if o=='global':
        return Security.global_right_have(str)
    return o.demand_right(str)

# default dictionary, if need to return to main screen
def DefaultLayout(dict = {}, maincontent = 'news'):
	a = ActiveContest(dict)
	d = {'name' : ['cover'], 
         'cover' :[{'name' : ['main'], 
                    'content' : [{'name' : [maincontent]} ], 
                    'loginspace' : [{'name' : ['loginform']}],
                    'headerspace' : [{'name': ['header']}]
                  }]
        }
	#d = {'name' : ['main'], 'content' : [{'name' : ['news']} ], 'login' : [{'name' : ['login']}]}
	if a:
		d['contestid'] = [str(a.id)]
	return d
