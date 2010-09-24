
from URLDictionary import *
from satori.client.common.remote import *
from datetime import datetime

# Module for database queries


def UserById(uid):
	return User(int(uid))

def ContestById(cid):
	return Contest.filter({'id' : int(cid)})[0]

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

#def explicit_right(object,role,right,moment=datetime.now()):
#    for p in Privilege.filter({'role':role, 'object':object, 'right':right}):
#        if not moment:
#            return True
#        if (not p.startOn or p.StartOn<datetime.now()) and (not p.finishOn or p.finishOn>datetime.now()):
#            return True
#    return False

# default dictionary, if need to return to main screen
def DefaultLayout(dict = {}, maincontent = 'news', **kwargs):
	a = ActiveContest(dict)
	params = kwargs
	params['name'] = [maincontent]
	d = {'name' : ['cover'], 
         'cover' :[{'name' : ['main'], 
                    'content' : [params], 
                    'loginspace' : [{'name' : ['loginform']}],
                    'headerspace' : [{'name': ['header']}]
                  }]
        }
	#d = {'name' : ['main'], 'content' : [{'name' : ['news']} ], 'login' : [{'name' : ['login']}]}
	if a:
		d['contestid'] = [str(a.id)]
	return d


def text2html(text):
    return text
    
