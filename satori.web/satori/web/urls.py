# vim:ts=4:sts=4:sw=4:expandtab
from django.conf.urls.defaults import *
from django.conf import settings

from satori.client.common import remote
remote.setup(settings.THRIFT_HOST, settings.THRIFT_PORT, settings.BLOB_PORT)

# Please keep the urlpatterns sorted.

contestadminpatterns = patterns('',
    (r'^$', 'satori.web.views.contest.admin.manage.load'),
    (r'^contestants$', 'satori.web.views.contest.admin.contestants.load'),
    (r'^news/(?P<id>\d+)$', 'satori.web.views.contest.admin.news.load'),
    (r'^questions$', 'satori.web.views.contest.contest.admin.questions.load'),
    (r'^questions/(?P<id>\d+)$', 'satori.web.views.contest.admin.editquestion.load'),
    (r'^ranking/(?P<id>\d+)$', 'satori.web.views.contest.admin.ranking.load'),
    (r'^subpage/(?P<id>\d+)$', 'satori.web.views.contest.admin.subpage.load'),
)

contestpatterns = patterns('',
    (r'^news$', 'satori.web.views.contest.news.load'),
    (r'^print', 'satori.web.views.contest.print.load'),
    (r'^problems$', 'satori.web.views.contest.problems.load'),
    (r'^problems/(?P<id>\d+)$', 'satori.web.views.contest.editproblems.load'),
    (r'^questions$', 'satori.web.views.contest.questions.load'),
    (r'^ranking/(?P<id>\d+)$', 'satori.web.views.contest.ranking.load'),
    (r'^results$', 'satori.web.views.contest.results.load'),
    (r'^results/(?P<id>\d+)$', 'satori.web.views.contest.editresults.load'),
    (r'^submit$', 'satori.web.views.contest.submit.load'),
    (r'^subpage/(?P<id>\d+)$', 'satori.web.views.contest.subpage.load'),

    (r'^admin/$', include(contestadminpatterns)),
)

adminpatterns = patterns('',
    (r'^news/(?P<id>\d+)$', 'satori.web.views.admin.news.load'),
    (r'^problems/(?P<id>\d+)$', 'satori.web.views.admin.problems.load'),
    (r'^ranking/(?P<id>\d+)$', 'satori.web.views.admin.ranking.load'),
    (r'^subpages/(?P<id>\d+)$', 'satori.web.views.admin.subpages.load'),
    (r'^users$', 'satori.web.views.admin.users.load'),
    (r'^users/(?P<id>\d+)$', 'satori.web.views.admin.edituser.load'),
)

urlpatterns = patterns('',
    (r'^$', 'satori.web.views.news.load'),
    (r'^contests$', 'satori.web.views.contests.load'), 
    (r'^login$', 'satori.web.views.login.load'), 
    (r'^logout$', 'satori.web.views.logout.load'), 
    (r'^news$', 'satori.web.views.news.load'), 
    (r'^profile$', 'satori.web.views.profile.load'), 
    (r'^subpage/(?P<id>\d+)$', 'satori.web.views.subpage.load'), 

    (r'admin/$', include(adminpatterns)),
    (r'contest/(?P<contestid>\d+)$', include(contestpatterns)),
)
