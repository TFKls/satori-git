# vim:ts=4:sts=4:sw=4:expandtab
from django.conf.urls.defaults import *
from django.conf import settings

from satori.client.common import remote
remote.setup(settings.THRIFT_HOST, settings.THRIFT_PORT, settings.BLOB_PORT)

import os
PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])

# Please keep the urlpatterns sorted.

contestpatterns = patterns('',
    url(r'^$', 'satori.web.views.contest.news.view', name='contest_main'),
#    url(r'assignments$', 'satori.web.views.contest.assignments.viewall', name='assignments'),
#    url(r'assignments/(?P<id>\d+)$', 'satori.web.views.contest.assignments.view', name='assignments_view'),
    url(r'news$', 'satori.web.views.contest.news.view', name='contest_news'),
    url(r'news/add$', 'satori.web.views.contest.news.add', name='contest_news_add'),
    url(r'news/(?P<id>\d+)/edit$', 'satori.web.views.contest.news.edit', name='contest_news_edit'),
#    url(r'news/(?P<id>\d+)/delete$', 'satori.web.views.contest.news.delete', name='contest_news_delete'),
    url(r'print', 'satori.web.views.contest.print.view', name='print'),
    url(r'problems$', 'satori.web.views.contest.problems.viewall', name='contest_problems'),
    url(r'problems/add$', 'satori.web.views.contest.problems.add', name='contest_problems_add'),
    url(r'problems/(?P<id>\d+)$', 'satori.web.views.contest.problems.view', name='contest_problems_view'),
    url(r'problems/(?P<id>\d+)/edit$', 'satori.web.views.contest.problems.edit', name='contest_problems_edit'),
    url(r'questions$', 'satori.web.views.contest.questions.view', name='questions'),
    url(r'answers$', 'satori.web.views.contest.answers.view', name='answers'),
    url(r'ranking/add$', 'satori.web.views.contest.ranking.add', name='ranking_add'),
    url(r'ranking/(?P<id>\d+)$', 'satori.web.views.contest.ranking.view', name='ranking'),
    url(r'ranking/(?P<id>\d+)/edit$', 'satori.web.views.contest.ranking.edit', name='ranking_edit'),
    url(r'ranking/(?P<id>\d+)/editparams/(?P<problem_id>\d+)$', 'satori.web.views.contest.ranking.editparams', name='ranking_editparams'),
    url(r'results$', 'satori.web.views.contest.results.view', name='results'),
    url(r'results/(?P<id>\d+)$', 'satori.web.views.contest.viewresult.view', name='view_result'),
    url(r'submit$', 'satori.web.views.contest.submit.view', name='submit'),
    url(r'subpage/add$', 'satori.web.views.contest.subpage.add', name='contest_subpage_add'),
    url(r'subpage/fileremove$', 'satori.web.views.contest.subpage.fileremove', name='contest_subpage_fileremove'),
    url(r'subpage/fileupload$', 'satori.web.views.contest.subpage.fileupload', name='contest_subpage_fileupload'),
    url(r'subpage/(?P<id>\d+)$', 'satori.web.views.contest.subpage.view', name='contest_subpage'),
    url(r'subpage/(?P<id>\d+)/edit$', 'satori.web.views.contest.subpage.edit', name='contest_subpage_edit'),
#    url(r'subpage/(?P<id>\d+)/delete$', 'satori.web.views.contest.subpage.delete', name='contest_subpage_delete'),
    url(r'contestants$', 'satori.web.views.contest.contestants.view', name='contestants'),
    url(r'manage$', 'satori.web.views.contest.manage.view', name='contest_manage'),
#    url(r'manage/rights$', 'satori.web.views.contest.manage.rights', name='contest_manage_rights'),
)

urlpatterns = patterns('',
    (r'^$', 'satori.web.views.news.view'),
    url(r'^configuration$', 'satori.web.views.configuration.view', name='configuration'),
    url(r'^news$', 'satori.web.views.news.view', name='news'),
    url(r'^news/add$', 'satori.web.views.news.add', name='news_add'),
    url(r'^news/(?P<id>\d+)/edit$', 'satori.web.views.news.edit', name='news_edit'),
#    url(r'^news/(?P<id>\d+)/delete$', 'satori.web.views.news.delete', name='news_delete'),
    url(r'^contest/select$', 'satori.web.views.select.view', name='select_contest'),
    url(r'^login$', 'satori.web.views.login.view', name='login'),
    url(r'^logout$', 'satori.web.views.logout.view', name='logout'),
    url(r'^news$', 'satori.web.views.news.view', name='news'),
    url(r'^profile$', 'satori.web.views.profile.view', name='profile'),
    url(r'^register$', 'satori.web.views.register.view', name='register'),
    url(r'^subpage/add$', 'satori.web.views.subpage.add', name='subpage_add'),
    url(r'^subpage/fileremove$', 'satori.web.views.subpage.fileremove', name='subpage_fileremove'),
    url(r'^subpage/fileupload$', 'satori.web.views.subpage.fileupload', name='subpage_fileupload'),
    url(r'^subpage/(?P<id>\d+)$', 'satori.web.views.subpage.view', name='subpage'),
    url(r'^subpage/(?P<id>\d+)/edit$', 'satori.web.views.subpage.edit', name='subpage_edit'),
    url(r'^(?P<mode>download|view)/(?P<model>[^/]+)/(?P<id>\d+)/(?P<attr_name>[^/]+)/(?P<file_name>[^/]+)$','satori.web.views.download.getfile', name='download'),
    url(r'^(?P<mode>download|view)/(?P<model>[^/]+)/(?P<id>\d+)/(?P<group_name>[^/]+)/(?P<attr_name>[^/]+)/(?P<file_name>[^/]+)$','satori.web.views.download.getfile_group', name='download_group'),
    (r'contest/(?P<contestid>\d+)/', include(contestpatterns)),

    (r'^files/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(PROJECT_PATH,'files')}),
)
