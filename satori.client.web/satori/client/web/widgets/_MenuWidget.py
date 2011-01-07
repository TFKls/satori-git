from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from _Widget import Widget

# left menu
class MenuWidget(Widget):
    pathName = 'menu'
    def __init__(self, params, path, content_path):
        self.htmlFile = 'htmls/menu.html'
        self.menuitems = []
        contest = ActiveContest(params)
        user = CurrentUser()
        cuser = CurrentContestant(params)
        def addwidget(check,label,wname,object = None,rights = ''):
            params_copy = deepcopy(params)
            d = follow(params_copy, content_path)
            if not check:
                return
            if object and not Allowed(object,rights):
                return
            f = { 'name' : [wname], 'override' : ["1"] };
            d['content'] = [f];
            self.menuitems.append([label,GetLink(params_copy,'')])

        def addlink(check,label,dict,object = None,rights=''):
            if not check:
                return
            if object and not Allowed(object,rights):
                return
            self.menuitems.append([label,GetLink(dict,'')])

        addwidget(True, 'News', 'news')
        addwidget(True, 'About', 'about')
        addwidget(CurrentUser(), 'Identities', 'identities')
        addwidget(not contest,'Select contest','selectcontest')
        addwidget(contest,'Problems','problems',contest,'VIEW')
        addwidget(cuser,'Submit','submit',contest,'VIEW')
        addwidget(contest,'Results','results',contest,'VIEW')
        if contest:
            for r in Ranking.filter({'contest':contest}):
                addlink(True,r.name,DefaultLayout(dict=params,maincontent='ranking',subid=[str(s.id)]),r,'VIEW')
        if contest:
            for s in Subpage.filter({'contest':contest,'is_announcement':False}):
                addlink(True,s.name,DefaultLayout(dict=params,maincontent='subpage',subid=[str(s.id)]),s,'VIEW')
        
        addwidget(contest,'Manage subpages','mancontest',contest,'MANAGE')
        if cuser:
            addwidget(user,'Manage news','mannews',contest,'MANAGE')
        else:
            addwidget(user,'Manage news','mannews','global','ADMIN')
        addwidget(contest,'Manage users & rights','manusers',contest,'MANAGE')
        addwidget(user, 'Problem repository','repository','global','ADMIN')
        addlink(contest,'Return to main',DefaultLayout())
