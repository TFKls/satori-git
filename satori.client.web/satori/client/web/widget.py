from copy import deepcopy
from URLDictionary import *
from queries import *
#from satori.core.models import *
from satori.client.common import *
from postmarkup import render_bbcode

class MetaWidget(type):
    allwidgets = {}
    
    def __init__(cls, name, bases, attrs):
        super(MetaWidget, cls).__init__(name, bases, attrs)
        #We don't want abstract class here
        if name != "Widget":
            if not hasattr(cls, 'pathName'):
                raise Exception('No pathName in widget ' + name)
            if cls.pathName in MetaWidget.allwidgets:
                raise Exception('Two widgets with the same pathName!') 
            MetaWidget.allwidgets[cls.pathName] = cls

class Widget:
    __metaclass__ = MetaWidget
    def __init__(self,params,path):
        pass

# returns a newly created widget of a given kind
    @staticmethod
    def FromDictionary(dict,path):
        if not ('name' in dict.keys()):
            dict = DefaultLayout(dict)
            #return dict #CoverWidget(dict, path)
        d = follow(dict,path)
        name = d['name'][0]
        return MetaWidget.allwidgets[name](dict,path)


# login box
class LoginWidget(Widget):
    pathName = 'loginform'
    def __init__(self, params, path):
        el = CurrentUser()
        if el:
            self.htmlFile = 'htmls/logged.html'
            self.name = el.fullname
        else:
            self.htmlFile = 'htmls/loginform.html'
            self.back_to = ToString(params)
            self.lw_path = path;

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
        addwidget(not contest,'Select contest','selectcontest')
        addwidget(contest,'Problems','problems',contest,'seeproblems')
        addwidget(cuser,'Submit','submit',contest,'submit')
        addwidget(contest,'Results','results',contest,'seeresults')
        addwidget(contest,'Ranking','ranking',contest,'seeranking')
        addwidget(cuser,'Manage contest','mancontest',contest,'manage')
        if cuser:
            addwidget(user,'Manage news','mannews',contest,'manage_news')
        else:
            addwidget(user,'Manage news','mannews',True,'manage_news')
        addwidget(contest,'Manage users','manusers',contest,'manage_users')
        addlink(contest,'Main screen',DefaultLayout())

# about table (to test ajah)
class AboutWidget(Widget):
    pathName = 'about'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/about.html'

# news table (a possible main content)
class NewsWidget(Widget):
    pathName = 'news'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/news.html'
        self.messages = []
        for m in MessageGlobal.filter():
            if not ActiveContest(params) or not m.mainscreenonly:
                self.messages.append({'type' : 'global', 'topic' : m.topic, 'content' : render_bbcode(m.content)})
        if (ActiveContest(params)):
            for m in MessageContest.filter(contest = ActiveContest(params)):
                self.messages.append({'type' : 'contest', 'topic' : m.topic, 'content' : render_bbcode(m.content)})
            
# results table (a possible main content)
class ResultsWidget(Widget):
    pathName = 'results'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/results.html'
        c = ActiveContest(params)
        _params = deepcopy(params)
        d = follow(_params,path)
        if not ('shown' in d.keys()):
            shown = []
        else:
            shown = d['shown']
        self.submits = []
        for o in Submit.filter(): # TODO: correct 
            if o.owner.contest==c:
                s = {}
                id = str(o.id)
                s["id"] = id
                s["time"] = o.time
                s["user"] = o.owner.user.fullname
                s["problem"] = o.problem.code
                s["status"] = o.shortstatus
                s["details"] = o.longstatus
                _shown = deepcopy(shown)
                if id in _shown:
                    s["showdetails"] = True
                    _shown.remove(id)
                else:
                    s["showdetails"] = False
                    _shown.append(id)
                _shown.sort()
                d['shown'] = _shown
                if _shown == []:
                    del d['shown']
                s["link"] = GetLink(_params,'')
                self.submits.append(s)

# ranking (a possible main content)
class RankingWidget(Widget):
    pathName = 'ranking'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/ranking.html'


class SubmitWidget(Widget):
    pathName = 'submit'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/submit.html'
        self.back_to = ToString(params)
        c = ActiveContest(params)
        self.problems = []
        self.cid = CurrentContestant(params).id
        for p in ProblemMapping.filter(contest=c):
            if Allowed(p,'submit'):
                self.problems.append(p)

class ManageUsersWidget(Widget):
    pathName = 'manusers'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/manusers.html'
        c = ActiveContest(params)
        self.accepted = list()
        self.pending = list()
        self.debug = "Debug: "
        for t in Contestant.filter(contest=c):
            if t.accepted:
                self.accepted.append(t.members())
                self.debug = self.debug + str(len(t.members()))
            else:
                self.pending.append(t.members())


class ManageNewsWidget(Widget):
    pathName = 'mannews'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/mannews.html'
        self.contest = ActiveContest(params)
        self.canglobal = Allowed(True,'managenews')
        self.messages = []
        d = follow(params,path)
        _params = deepcopy(params)
        _d = follow(_params,path)
        if 'edit' in d.keys():
            self.editing = True
            try:
                msg = MessageGlobal(d['edit'][0])
            except MessageGlobal.DoesNotExist:
                msg = MessageContest(d['edit'][0])
            self.msgtopic = msg.topic
            self.msgcontent = msg.content
            self.msgid = msg.id
            del _d['edit'];
        self.back_to = ToString(_params);
        for m in MessageGlobal.filter():
            if not ActiveContest(params) or not m.mainscreenonly:
                self.messages.append({'id' : m.id, 'type' : 'global', 'topic' : m.topic, 'content' : render_bbcode(m.content), 'time' : m.time, 'canedit' : Allowed(m,'edit')})
        for m in MessageContest.filter(contest = ActiveContest(params)):
                self.messages.append({'id' : m.id, 'type' : 'contest', 'topic' : m.topic, 'content' : render_bbcode(m.content), 'time' : m.time, 'canedit' : Allowed(m,'edit')})
        for md in self.messages:
            if md['canedit']:
                _d['edit'] = [str(md['id'])]
                md['editlink'] = GetLink(_params,'')

class ManageContestWidget(Widget):
    pathName = 'mancontest'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/mancontest.html'

class ProblemsWidget(Widget):
    pathName = 'problems'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/problems.html'
        c = ActiveContest(params)
        self.problems = ProblemMapping.filter(contest=c)

# contest selection screen (a possible main content)
class SelectContestWidget(Widget):
    pathName = 'selectcontest'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/selectcontest.html'
        self.participating = []
        self.mayjoin = []
        self.other = []
        self.user = CurrentUser()
        self.params = params
        self.path = path
        for c in Contest.filter():
            cu = MyContestant(c)
            d = DefaultLayout()
            d['contestid'] = [str(c.id)]
            if cu:
                self.participating.append([c,cu,GetLink(d,'')])
            else:
                mayjoin = Allowed(c,"APPLY")
                self.other.append([c,mayjoin,GetLink(d,'')])

# base widget
class MainWidget(Widget):
    pathName = 'main'
    def __init__(self, params, path):
        _params = follow(params,path)
        self.htmlFile = 'htmls/index.html'
        self.loginform = LoginWidget(params,path)
        if not ('content' in _params.keys()):
            _params['content'] = [{'name' : ['news']}]
        self.menu = MenuWidget(params,path,path)
        self.content = Widget.FromDictionary(params,path+'|content(0)');
        self.params = _params

# cover widget
class CoverWidget(Widget):
    pathName = 'cover'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/cover.html'
        d = DefaultLayout(params)
        self.cover = Widget.FromDictionary(params,'cover(0)');
#        self.startLink = GetLink(d,'')
