from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class AnswersWidget(Widget):
    pathName = 'answers'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/answers.html'
        self.contest = ActiveContest(params)
        d = follow(params,path)
        _params = deepcopy(params)
        _d = follow(_params,path)
        allq = Question.filter(QuestionStruct(contest=c))
        if 'edit' in d.keys():
            self.editing = Question.filter({'id' : int(d['edit'][0])})[0]
            del _d['edit']
        self.back_to = ToString(_params);
        c = self.contest
        if not c:
            raise RuntimeError('') # TODO
        self.problems = ProblemMapping.filter(ProblemMappingStruct(contest=c))
        self.questions = []
        
        for q in allq:
            r = {'q' : q}
            if q.answer:
                r['answer'] = text2html(q.answer)
            else:
                r['answer'] = None
            _d['edit'] = [str(r['q'].id)]
            r['editlink'] = GetLink(_params,'')
            self.questions.append(r)
        self.questions.sort(key=lambda question : question['q'].date_created, reverse=True)

