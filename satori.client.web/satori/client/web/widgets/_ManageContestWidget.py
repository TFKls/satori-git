from _Widget import Widget
from satori.client.web.queries import *

class ManageContestWidget(Widget):
    pathName = 'mancontest'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/mancontest.html'
        c = ActiveContest(params)
        self.contest = c
        self.accepted = list()
        self.pending = list()
        self.back_to = ToString(params)
        self.path = path
        self.subpages = []
        for s in Subpage.get_for_contest(c,False):
            editlink = ToString(DefaultLayout(dict=params,maincontent='editsubpage',edit=[str(s.id)]))
            self.subpages.append([s,editlink])
        self.rankings = []
        self.subpages.sort(key=lambda s : s[0].order)
        self.addsubpagelink = ToString(DefaultLayout(dict=params,maincontent='editsubpage',contest=c))


        for r in Ranking.filter(RankingStruct(contest=c)):
            editlink = ToString(DefaultLayout(dict=params,maincontent='editranking',edit=[str(r.id)]))
            self.rankings.append([r,editlink])
        self.addrankinglink = ToString(DefaultLayout(dict=params,maincontent='editranking',contest=c))
            
        authenticated = Security.authenticated()
        
        if Privilege.get(authenticated, c, 'JOIN') is not None:
            jo = 3
        elif Privilege.get(authenticated, c, 'APPLY') is not None:
            jo = 2
        elif Privilege.get(authenticated, c, 'VIEW') is not None:
            jo = 1
        else:
            jo = 0
        self.joining_options=[["invisible","Contest invisible",jo==0],["invitation","Only when added",jo==1],["moderated","By acceptation",jo==2],["public","Freely",jo==3]]

        if Privilege.get(authenticated, c, 'ASK_QUESTIONS') is not None:
            qo = 2
        elif Privilege.get(c.contestant_role, c, 'ASK_QUESTIONS') is not None:
            qo = 1
        else:
            qo = 0
        self.question_options=[["disabled","Questions disabled",qo==0],["contestants","Contestants only",qo==1],["everyone","All users",qo==2]]

        self.anonymous_view = Privilege.get(Security.anonymous(), c, 'VIEW') is not None

