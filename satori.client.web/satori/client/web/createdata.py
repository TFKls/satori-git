from django.http import HttpResponse
from satori.client.common.remote import *
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
    Privilege.create_global(role = paladin, right='ADMIN')
    token = Security.login(login='paladin', password='paladin')

    checker = Security.machine_register(secret='sekret', name='checker_one', address='0.0.0.0', netmask='0.0.0.0')
    
    token_container.set_token(token)
    c2 = Contest.create_contest(name = 'Kontest prywatny')
    c3 = Contest.create_contest(name = 'Kontest moderowany')
    c4 = Contest.create_contest(name = 'Kontest publiczny')
    Privilege.create({'object': c2, 'role': paladin, 'right':'JOIN'})
    Privilege.create({'object': c3, 'role': paladin, 'right':'APPLY'})
    Privilege.create({'object': c4, 'role': paladin, 'right':'JOIN'})
    Privilege.create({'object': c2, 'role': paladin, 'right':'MANAGE'})
    cc2 = c2.join_contest()
    
    
    p1 = Problem.create({'name': "SORT", 'description': "Zadanie o sortowaniu"})
    p2 = Problem.create({'name': "COW", 'description': "Zadanie o krowie"})
    p3 = Problem.create({'name': "WUWU", 'description': "Zadanie o wuwuzeli"})
    ts1 = TestSuite.create({'problem': p1, 'name': "Testy do SORT", 'dispatcher' : 'satori.core.judge_dispatcher.default_serial_dispatcher', 'accumulators' : 'satori.core.judge_dispatcher.default_status_accumulator'})
    for i in range(1,4):
        t = Test.create({'problem':p1, 'name':"Test "+str(i), 'description':"Test numer "+str(i)+" do zadania SORT."})
        TestMapping.create({'suite':ts1, 'test':t, 'order':i})
    tp2 = []
    ts2 = TestSuite.create({'problem': p2, 'name': "Testy do COW", 'dispatcher' : 'satori.core.judge_dispatcher.default_serial_dispatcher', 'accumulators' : 'satori.core.judge_dispatcher.default_status_accumulator'})
    for i in range(1,2):
        t = Test.create({'problem':p2, 'name':"Test "+str(i), 'description':"Test numer "+str(i)+" do zadania COW."})
        TestMapping.create({'suite':ts2, 'test':t, 'order':i})
    tp3 = []
    ts3 = TestSuite.create({'problem': p3, 'name': "Testy do WUWU", 'dispatcher' : 'satori.core.judge_dispatcher.default_serial_dispatcher', 'accumulators' : 'satori.core.judge_dispatcher.default_status_accumulator'})
    for i in range(1,3):
        t = Test.create({'problem':p3, 'name':"Test "+str(i), 'description':"Test numer "+str(i)+" do zadania WUWU."})
        TestMapping.create({'suite':ts3, 'test':t, 'order':i})
    
    ProblemMapping.create({'problem':p1, 'contest':c4, 'code':"A", 'title':"Harry Potter i sortownia smieci", 'default_test_suite':ts1})
    ProblemMapping.create({'problem':p2, 'contest':c4, 'code':"B", 'title':"Harry Potter i krowa z Albanii", 'default_test_suite':ts2})
    ProblemMapping.create({'problem':p3, 'contest':c4, 'code':"C", 'title':"Harry Potter i wuwuzele", 'default_test_suite':ts3})
    MessageGlobal.create({'topic':"Wiadomosc pierwsza", 'content':"BZZZZZ!", 'mainscreenonly':True})
    MessageGlobal.create({'topic':"Wiadomosc systemowa", 'content':"Oglaszamy, ze za 5 minuBZZZZZ!", 'mainscreenonly':False})
    MessageContest.create({'topic':"Wiadomosc powitalna", 'content':"Publiczne BZZZZZ!", 'contest':c4})
    return HttpResponse('OK!')
