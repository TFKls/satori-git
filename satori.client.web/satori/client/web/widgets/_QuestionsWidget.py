from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class QuestionsWidget(Widget):
    pathName = 'questions'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/questions.html'
        self.contest = ActiveContest(params)
        d = follow(params,path)
        self.back_to = ToString(params);
        c = self.contest
        if not c:
            raise RuntimeError('') # TODO
        allq = Question.filter(QuestionStruct(contest=c))
        self.problems = ProblemMapping.filter(ProblemMappingStruct(contest=c))
        self.questions = []
        for q in allq:
            r = {'q' : q}
            if q.answer:
                r['answer'] = text2html(q.answer)
            else:
                r['answer'] = None
#            r['public'] = MyContestant(c).parent_role
            self.questions.append(r)
        self.questions.sort(key=lambda question : question['q'].date_created, reverse=True)
#        for m in MessageGlobal.filter():
#            if not ActiveContest(params) or not m.mainscreenonly:
#                self.messages.append({'id' : m.id, 'type' : 'global', 'topic' : m.topic, 'content' : m.content, 'time' : m.time, 'canedit' : Allowed(m,'edit')})
#        if ActiveContest(params):
#            for m in MessageContest.filter({'contest':ActiveContest(params)}):
#                    self.messages.append({'id' : m.id, 'type' : 'contest', 'topic' : m.topic, 'content' : m.content, 'time' : m.time, 'canedit' : Allowed(m,'edit')})
        