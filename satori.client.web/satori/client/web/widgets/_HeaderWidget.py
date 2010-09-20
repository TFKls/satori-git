from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

# header menu
class HeaderWidget(Widget):
    pathName = 'header'
    def __init__(self, params, path, content_path):
        self.htmlFile = 'htmls/header.html'
        self.menuitems = []
        contest = ActiveContest(params)
        user = CurrentUser()
        cuser = CurrentContestant(params)
        def addwidget(check,label,wname, isLeft = False, object = None,rights = ''):
            params_copy = deepcopy(params)
            d = follow(params_copy, content_path)
            if not check:
                return
            if object and not Allowed(object,rights):
                return
            f = { 'name' : [wname], 'override' : ["1"] };
            d['content'] = [f]
            self.menuitems.append([label,GetLink(params_copy,''), isLeft])

        addwidget(True, 'News', 'news', True)
        addwidget(True, 'Contests', 'selectcontest', True)
        addwidget(user, 'Virtual Contests', 'selectvcontests', True)
        addwidget(user, 'Profile', 'profile', False)
        addwidget(not user, 'Sign In', 'loginform', False)
        addwidget(not user, 'Register', 'registerform', False)
        if user:
            self.username = user.fullname
        if contest:
            self.contest = contest.name
