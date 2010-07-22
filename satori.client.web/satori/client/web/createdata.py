from django.http import HttpResponse
from satori.client.common import *

def create(request):
#    ProblemMapping.objects.all().delete()
#    Problem.objects.all().delete()
#    Contestant.objects.all().delete()
#    Contest.objects.all().delete()
#    User.objects.all().delete()
#    MessageGlobal.objects.all().delete()
#    MessageContest.objects.all().delete()
    User = User
    for object in User.filter():
        object.delete()
    Contest = Contest
    for object in Contest.filter():
        object.delete()
    Contestant = Contestant
    for object in Contestant.filter():
        object.delete()
    Problem = Problem
    for object in Problem.filter():
        object.delete()
    ProblemMapping = ProblemMapping
    for object in ProblemMapping.filter():
        object.delete()
    MessageGlobal = MessageGlobal
    for object in MessageGlobal.filter():
        object.delete()
    MessageContest = MessageContest
    for object in MessageContest.filter():
        object.delete()
    RoleMapping = RoleMapping
    for object in RoleMapping.filter():
        object.delete()
    paladin = User.create(fullname='Lech Duraj', login='paladin')
    User.create(fullname='Edgsger W. Dijkstra', login = 'dijkstra')
    c2 = Contest.create(name = 'Kontest prywatny', joining = 'Private')
    c3 = Contest.create(name = 'Kontest moderowany', joining = 'Moderated')
    c4 = Contest.create(name = 'Kontest publiczny', joining = 'Public')
    cc2 = Contestant.create(contest = c2, accepted = True)
    RoleMapping.create(parent = cc2, child = paladin)
    cc3 = Contestant.create(contest = c3, accepted = True)
    RoleMapping.create(parent = cc3, child = paladin)
    cc4 = Contestant.create(contest = c4, accepted = True)
    RoleMapping.create(parent = cc4, child = paladin)
    p1 = Problem.create(name = "SORT", description = "Zadanie o sortowaniu")
    p2 = Problem.create(name = "COW", description = "Zadanie o krowie")
    p3 = Problem.create(name = "WUWU", description = "Zadanie o wuwuzeli")
    ProblemMapping.create(problem = p1, contest = c4, code = "A", title = "Harry Potter i sortownia smieci")
    ProblemMapping.create(problem = p2, contest = c4, code = "B", title = "Harry Potter i krowa z Albanii")
    ProblemMapping.create(problem = p3, contest = c4, code = "C", title = "Harry Potter i wuwuzele")
    MessageGlobal.create(topic = "Wiadomosc pierwsza", content = "BZZZZZ!", mainscreenonly = True)
    MessageGlobal.create(topic = "Wiadomosc systemowa", content = "Oglaszamy, ze za 5 minuBZZZZZ!", mainscreenonly = False)
    MessageContest.create(topic = "Wiadomosc powitalna", content = "Publiczne BZZZZZ!", contest = c4)
    return HttpResponse('OK!')
