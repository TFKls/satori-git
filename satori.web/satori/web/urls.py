# vim:ts=4:sts=4:sw=4:expandtab
from django.conf.urls.defaults import *
from django.conf import settings

from satori.client.common import remote
remote.setup(settings.THRIFT_HOST, settings.THRIFT_PORT, settings.BLOB_PORT)

import os
PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])

# Please keep the urlpatterns sorted.

contestadminpatterns = patterns('',
    (r'^$', 'satori.web.views.contest.admin.manage.view'),
    (r'^contestants$', 'satori.web.views.contest.admin.contestants.view'),
    (r'^news/(?P<id>\d+)$', 'satori.web.views.contest.admin.news.view'),
    (r'^questions$', 'satori.web.views.contest.contest.admin.questions.view'),
    (r'^questions/(?P<id>\d+)$', 'satori.web.views.contest.admin.editquestion.view'),
    (r'^ranking/(?P<id>\d+)$', 'satori.web.views.contest.admin.ranking.view'),
    (r'^subpage/(?P<id>\d+)$', 'satori.web.views.contest.admin.subpage.view'),
)

contestpatterns = patterns('',
    (r'^news$', 'satori.web.views.contest.news.view'),
    (r'^print', 'satori.web.views.contest.print.view'),
    (r'^problems$', 'satori.web.views.contest.problems.view'),
    (r'^problems/(?P<id>\d+)$', 'satori.web.views.contest.editproblems.view'),
    (r'^questions$', 'satori.web.views.contest.questions.view'),
    (r'^ranking/(?P<id>\d+)$', 'satori.web.views.contest.ranking.view'),
    (r'^results$', 'satori.web.views.contest.results.view'),
    (r'^results/(?P<id>\d+)$', 'satori.web.views.contest.editresults.view'),
    (r'^submit$', 'satori.web.views.contest.submit.view'),
    (r'^subpage/(?P<id>\d+)$', 'satori.web.views.contest.subpage.view'),

    (r'^admin/$', include(contestadminpatterns)),
)

adminpatterns = patterns('',
    (r'^news/(?P<id>\d+)$', 'satori.web.views.admin.news.view'),
    (r'^problems/(?P<id>\d+)$', 'satori.web.views.admin.problems.view'),
    (r'^ranking/(?P<id>\d+)$', 'satori.web.views.admin.ranking.view'),
    (r'^subpages/(?P<id>\d+)$', 'satori.web.views.admin.subpages.view'),
    (r'^users$', 'satori.web.views.admin.users.view'),
    (r'^users/(?P<id>\d+)$', 'satori.web.views.admin.edituser.view'),
)

urlpatterns = patterns('',
    (r'^$', 'satori.web.views.news.view'),
#    (r'^contests$', 'satori.web.views.contests.view'), 
#    (r'^login$', 'satori.web.views.login.view'), 
#    (r'^logout$', 'satori.web.views.logout.view'), 
    url(r'^news$', 'satori.web.views.news.view', name='news'), 
#    (r'^profile$', 'satori.web.views.profile.view'), 
#    (r'^subpage/(?P<id>\d+)$', 'satori.web.views.subpage.view'), 

#    (r'admin/$', include(adminpatterns)),
#    (r'contest/(?P<contestid>\d+)$', include(contestpatterns)),

    (r'^files/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(PROJECT_PATH,'files')}),
)
