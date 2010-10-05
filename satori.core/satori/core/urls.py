# vim:ts=4:sts=4:sw=4:expandtab

from django.conf.urls.defaults import *
from satori.core.models import *

# import os

# PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # (r'^blob/(?P<model>[^/]+)/(?P<id>\d+)/(?P<name>[^/]+)$','satori.core.blob.server'),
    (r'^blob/(?P<model>[^/]+)/(?P<id>\d+)/(?P<group>[^/]+)/(?P<name>[^/]+)$','satori.core.blob.server'),
    (r'^blob/upload$','satori.core.blob.upload'),
    (r'^blob/download/(?P<hash>[^/]+)$','satori.core.blob.download'),
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # (r'^admin/', include(admin.site.urls)),
)
