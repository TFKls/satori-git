from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class EditProblemWidget(Widget):
    pathName = 'editproblem'
    def __init__(self,params,path):
        self.htmlFile='htmls/editproblem.html'
        d = follow(params,path)
        id = int(d['problemid'][0])
        p = Problem.filter({'id':id})[0]
        self.p = p
        self.checkers = Global.get_instance().checkers_get_list()
        self.defjudge = p.default_test_data_get_blob_hash("judge")
