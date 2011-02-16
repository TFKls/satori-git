# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response

@contest_view
def view(request, general_page_overview):
    contest = general_page_overview.contest
    results_aux = contest.get_all_results()
    results = results_aux.results
    rescount = results_aux.count
    return render_to_response('results.html',{ 'general_page_overview' : general_page_overview, 'results' : results })
