from cdata.models import *
from django.http import HttpResponse

def create(request):
	User.objects.all().delete()
	paladin = User(id = '1',login='paladin',password='aaa',fullname='Lech Duraj')
	paladin.save()
	User(id = '2',login='dijkstra',password='d',fullname='Edgsger W. Dijkstra').save()
	Contest.objects.all().delete()
	c1 = Contest(id = '1', name = 'Kontest nieobecny', joining = 0)
	c2 = Contest(id = '2', name = 'Kontest prywatny', joining = 1)
	c3 = Contest(id = '3', name = 'Kontest moderowany', joining = 2)
	c4 = Contest(id = '4', name = 'Kontest publiczny', joining = 3)
	c1.save()
	c2.save()
	c3.save()
	c4.save()
	ConUser.objects.all().delete()
	ConUser(user = paladin, contest = c1, is_admin = True, accepted = True).save()
	ConUser(user = paladin, contest = c2, is_admin = True, accepted = True).save()
	ConUser(user = paladin, contest = c3, is_admin = True, accepted = True).save()
	ConUser(user = paladin, contest = c4, is_admin = True, accepted = True).save()
	return HttpResponse('OK!')
