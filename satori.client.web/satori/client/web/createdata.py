from django.http import HttpResponse
from satori.client.common.remote import *
from os.path import getsize,dirname
import crypt

def create(request):
#    ProblemMapping.objects.all().delete()
#    Problem.objects.all().delete()
#    Contestant.objects.all().delete()
#    Contest.objects.all().delete()
#    User.objects.all().delete()
#    MessageGlobal.objects.all().delete()
#    MessageContest.objects.all().delete()
#    for object in Privilege.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in Machine.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in User.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in Contest.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in Contestant.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in Problem.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in ProblemMapping.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in MessageGlobal.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in MessageContest.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in RoleMapping.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in Role.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in Test.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in TestSuite.filter():
#        try:
#            object.delete()
#        except:
#            pass
#    for object in TestMapping.filter():
#        try:
#            object.delete()
#        except:
#            pass

    token_container.set_token(Security.login(login='admin', password='admin'))
        
    paladin = Security.register(login='paladin', fullname='Lech Duraj', password='paladin')
    dijkstra = Security.register(fullname='Edgsger W. Dijkstra', login = 'dijkstra', password='dijkstra')
    Privilege.global_grant(paladin, 'ADMIN')
    token = Security.login(login='paladin', password='paladin')

    checker = Security.machine_register(secret='sekret', name='checker_one', address='0.0.0.0', netmask='0.0.0.0')


    
    token_container.set_token(token)
    Privilege.create({'object' : Global.get_instance(), 'role' : Security.anonymous(), 'right' : 'VIEW_BASICS'})
    c2 = Contest.create_contest(name = 'Kontest prywatny')
    c3 = Contest.create_contest(name = 'Kontest moderowany')
    c4 = Contest.create_contest(name = 'Kontest publiczny')
    Privilege.grant(paladin, c2, 'JOIN')
    Privilege.grant(paladin, c3, 'APPLY')
    Privilege.grant(paladin, c4, 'JOIN')
    Privilege.grant(paladin, c2, 'MANAGE')
    cc2 = c2.join_contest()
    
    g = Global.get_instance()
    print dirname(__file__)+'/default_judge.py'
    g.checkers_set_blob_path('Default judge', dirname(__file__)+'/../../../../satori.judge/satori/judge/default_judge.py')
    dj = g.checkers_get_blob_hash('Default judge')
    
    p1 = Problem.create({'name': "TEST", 'description': "Zadanie bez bajki"})
    p2 = Problem.create({'name': "COW", 'description': "Zadanie o krowie"})
    p3 = Problem.create({'name': "WUWU", 'description': "Zadanie o wuwuzeli"})
    ts1 = TestSuite.create({'problem': p1, 'name': "Testy do TEST :)", 'dispatcher' : 'SerialDispatcher', 'accumulators' : 'StatusAccumulator,StatusReporter'})
    t0 = Test.create({'problem': p1, 'name' : 'Test 0','description' : 'Jedyny test do zadania bez bajki.'})
    t0.oa_set_blob_hash('judge', dj)
    t0.oa_set_blob_path('input', dirname(__file__)+'/testfiles/X0.in')
    t0.oa_set_blob_path('hint', dirname(__file__)+'/testfiles/X0.out')
    t0.oa_set_str('time','1000')
    t0.oa_set_str('memory','8192')
    TestMapping.create({'suite':ts1, 'test':t0, 'order':1})
    
    tp2 = []
    ts2 = TestSuite.create({'problem': p2, 'name': "Testy do COW", 'dispatcher' : 'SerialDispatcher', 'accumulators' : 'StatusAccumulator,StatusReporter'})
    for i in range(1,2):
        t = Test.create({'problem':p2, 'name':"Test "+str(i), 'description':"Test numer "+str(i)+" do zadania COW."})
        TestMapping.create({'suite':ts2, 'test':t, 'order':i})
    tp3 = []
    ts3 = TestSuite.create({'problem': p3, 'name': "Testy do WUWU", 'dispatcher' : 'SerialDispatcher', 'accumulators' : 'StatusAccumulator,StatusReporter'})
    for i in range(1,3):
        t = Test.create({'problem':p3, 'name':"Test "+str(i), 'description':"Test numer "+str(i)+" do zadania WUWU."})
        TestMapping.create({'suite':ts3, 'test':t, 'order':i})
    
    ProblemMapping.create({'problem':p1, 'contest':c2, 'code':"X", 'title':"Bez bajki", 'default_test_suite':ts1})
    ProblemMapping.create({'problem':p2, 'contest':c4, 'code':"B", 'title':"Harry Potter i krowa z Albanii", 'default_test_suite':ts2})
    ProblemMapping.create({'problem':p3, 'contest':c4, 'code':"C", 'title':"Harry Potter i wuwuzele", 'default_test_suite':ts3})
    MessageGlobal.create({'topic':"Wiadomosc pierwsza", 'content':"BZZZZZ!", 'mainscreenonly':True})
    MessageGlobal.create({'topic':"Wiadomosc systemowa", 'content':"Oglaszamy, ze za 5 minuBZZZZZ!", 'mainscreenonly':False})
    MessageContest.create({'topic':"Wiadomosc powitalna", 'content':"Publiczne BZZZZZ!", 'contest':c4})
    return HttpResponse('OK!')
