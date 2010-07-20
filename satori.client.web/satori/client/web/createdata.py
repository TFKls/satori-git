from django.http import HttpResponse
from satori.client.common import classes

def create(request):
#    ProblemMapping.objects.all().delete()
#    Problem.objects.all().delete()
#    Contestant.objects.all().delete()
#    Contest.objects.all().delete()
#    User.objects.all().delete()
#    MessageGlobal.objects.all().delete()
#    MessageContest.objects.all().delete()
    User = classes.User
    Contest = classes.Contest
    Contestant = classes.Contestant
    Problem = classes.Problem
    ProblemMapping = classes.ProblemMapping
    MessageGlobal = classes.MessageGlobal
    MessageContest = classes.MessageContest
    paladin = User.create(fullname='Lech Duraj', login='paladin')
    User.create(fullname='Edgsger W. Dijkstra', login = 'dijkstra')
    c2 = Contest.create(name = 'Kontest prywatny', joining = 'Private')
    c3 = Contest.create(name = 'Kontest moderowany', joining = 'Moderated')
    c4 = Contest.create(name = 'Kontest publiczny', joining = 'Public')
    Contestant.create(user = paladin, contest = c2, accepted = True)
    Contestant.create(user = paladin, contest = c3, accepted = True)
    Contestant.create(user = paladin, contest = c4, accepted = True)
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
