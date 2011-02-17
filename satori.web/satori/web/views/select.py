# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response

@general_view
def view(request, page_info):
    if request.method=="POST":
        for id in request.POST.keys():
            contest = Contest(int(id))
            contest.join()
    managed = []
    participating = []
    other = []
    for contest_info in Web.get_contest_list():
        if contest_info.is_admin:
            managed.append(contest_info)
        elif contest_info.contestant:
            participating.append(contest_info)
        else:
            other.append(contest_info)
    return render_to_response('select_contest.html', {'page_info' : page_info, 'managed' : managed, 'participating' : participating, 'other' : other})
