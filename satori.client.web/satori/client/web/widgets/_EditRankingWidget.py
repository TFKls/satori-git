from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class EditRankingWidget(Widget):
    pathName = 'editranking'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/editranking.html'
        self.contest = ActiveContest(params)
        d = follow(params,path)
        if 'edit' in d.keys():
            self.editing = Ranking.filter({'id' : int(d['edit'][0])})[0]
        else:
            self.editing = None
        self.aggregators = Global.get_instance().get_aggregators().keys()
        self.back_to = ToString(params)
        