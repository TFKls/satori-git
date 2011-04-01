# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

@contest_view
def view(request, page_info):
    contest = page_info.contest
    questions = []
    for q in Question.filter(QuestionStruct(contest=contest)):
        if page_info.contest_is_admin:
            public = Privilege.get(contest.contestant_role,q,'VIEW')
        else:
            public = (q.inquirer != page_info.contestant)
        questions.append([q,public])
    return render_to_response('questions.html', {'page_info' : page_info, 'questions' : questions})


@contest_view
def ask(request, page_info):
    contest = page_info.contest
    problems = Web.get_problem_mapping_list(contest=contest)
    problems.sort(key=lambda p:p.problem_mapping.code)
    
    class QuestionForm(forms.Form):
        choices = []
        choices.append(['none','Select a problem'])
        choices.append(['general','General/Technical'])
        for p in problems:
            pm = p.problem_mapping
            choices.append([pm.id, pm.code+' - '+pm.title])
        problem = forms.ChoiceField(choices=choices, required=True)
        content = forms.CharField(widget=forms.Textarea, required=True, label="Question")
        def clean(self):
            data = self.cleaned_data
            if data['problem']=='none':
                self._errors['problem'] = ['Please choose a problem.']
                del data['problem']
            return data
            
    if request.method=="POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if data['problem']=='general':
                problem = None
            else:
                problem = ProblemMapping(int(data['problem']))
            Question.create(QuestionStruct(contest=contest,problem=problem,content=data['content']))
            return HttpResponseRedirect(reverse('questions',args=[contest.id]))    
    else:    
        form = QuestionForm()
    return render_to_response('question_ask.html', { 'page_info' : page_info, 'form' : form })
    

@contest_view
def answer(request, page_info, id):
    contest = page_info.contest
    question = Question(int(id))
    
    class AnswerForm(forms.Form):
        content = forms.CharField(required=True, widget=forms.Textarea)
        answer = forms.CharField(required=False, widget=forms.Textarea)
    if request.method=="POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            question.content = form.cleaned_data["content"]
            question.answer = form.cleaned_data["answer"]
            if 'make_public' in request.POST.keys():
                question2 = Question.create(QuestionStruct(contest=contest,problem=question.problem,content=question.content))
                question2.answer = question.answer
                Privilege.grant(contest.contestant_role,question2,'VIEW')
            return HttpResponseRedirect(reverse('questions',args=[contest.id]))    
    else:
        form = AnswerForm(initial={'content' : question.content, 'answer' : question.answer})
    
    return render_to_response('question_answer.html', { 'page_info' : page_info, 'form' : form, 'question' : question })
    