from copy import deepcopy
from URLDictionary import *
from queries import *
from satori.core.models import *

allwidgets = {}	

class Widget:
	def __init(self,params,path):
		pass

# returns a newly created widget of a given kind
	@staticmethod
	def FromDictionary(dict,path):
		if not ('name' in dict.keys()):
			dict = DefaultLayout(dict)
		d = follow(dict,path)
		name = d['name'][0]
		return allwidgets[name](dict,path)			


# login box
class LoginWidget(Widget):
	def __init__(self, params, path):
		el = CurrentUser()
		if el:
			self.htmlFile = 'htmls/logged.html'			
			self.name = el.fullname
		else:
			self.htmlFile = 'htmls/loginform.html'
			self.back_to = ToString(params)
	
	
# left menu
class MenuWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/menu.html'
		self.menuitems = []
		contest = ActiveContest(params)
		user = CurrentUser()
		cuser = CurrentContestant(params)
		
		def addwidget(check,label,wname,object = None,rights = ''):
			if not check:
				return
			if object and not Allowed(object,rights):
				return
			d = DefaultLayout(params)
			f = { 'name' : [wname] };
			d['content'] = [f];
			self.menuitems.append([label,GetLink(d,'')])
			
		def addlink(check,label,dict,object = None,rights=''):
			if not check:
				return
			if object and not Allowed(object,rights):
				return
			self.menuitems.append([label,GetLink(dict,'')])
			
		addwidget(not contest,'Select contest','selectcontest')
		addwidget(cuser,'Submit','submit',contest,'submit')
		addwidget(contest,'Results','results',contest,'seeresults')
		addwidget(contest,'Ranking','ranking',contest,'seeranking')
		addwidget(contest,'Manage users','manusers',contest,'manage_users')
		addwidget(contest,'Manage problems','manproblems',contest,'manage_problems')
		addlink(contest,'Main screen',DefaultLayout())			
			
# news table (a possible main content)
class NewsWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/news.html'


# results table (a possible main content)
class ResultsWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/results.html'


# ranking (a possible main content)
class RankingWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/ranking.html'


class SubmitWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/submit.html'


class ManageUsersWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/manusers.html'
		c = ActiveContest(params)
		self.accepted = ConUser.objects.filter(contest=c,accepted=True)
		self.pending = ConUser.objects.filter(contest=c,accepted=False)
		
class ManageProblemsWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/manproblems.html'


# contest selection screen (a possible main content)
class SelectContestWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/selectcontest.html'
		self.participating = []
		self.mayjoin = []
		self.other = []
		self.user = CurrentUser()
		for c in Contest.objects.all():
			cu = None
			if self.user:
				try:
					cu = ConUser.objects.get(user=self.user.id, contest=c.id)
				except ConUser.DoesNotExist:
					pass
			d = DefaultLayout()
			d['contestid'] = [str(c.id)]				
			if cu and c.joining!=0 and cu.accepted:
				self.participating.append([c,cu,GetLink(d,'')])
			elif c.joining == 2 or c.joining == 3:
				self.mayjoin.append([c,cu,GetLink(d,'')])
			else:
				self.other.append([c,cu,GetLink(d,'')])

# base widget
class MainWidget(Widget):
	def __init__(self, params, path):
		self.htmlFile = 'htmls/index.html'		
		self.loginform = LoginWidget(params,path)
		self.menu = MenuWidget(params,path)
		if not ('content' in params.keys()):
			params['content'] = [{'name' : ['news']}]
		self.content = Widget.FromDictionary(params,'content');
		self.params = params

		
allwidgets = {
'main' : MainWidget, 
'menu' : MenuWidget, 'news' : NewsWidget, 
'selectcontest' : SelectContestWidget, 
'loginform' : LoginWidget, 
'ranking' : RankingWidget, 
'results' : ResultsWidget, 
'submit' : SubmitWidget,
'manusers' : ManageUsersWidget,
'manproblems' : ManageProblemsWidget
}	
