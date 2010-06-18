from django.conf.urls.defaults import *
from satori.core.models import *

import os

PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
#     (r'^$', 'satori.client.web.main.loaddefault'),
	(r'^create/','satori.client.web.createdata.create'),
	(r'^admin/', include(admin.site.urls)),
	(r'^files/(?P<path>.*)/$', 'django.views.static.serve',
        {'document_root': os.path.join(PROJECT_PATH,'files')}),        
	(r'^files/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(PROJECT_PATH,'files')}),
	(r'^process/(?P<argstr>.*)/$','satori.client.web.main.loadPOST'),
	(r'^process/(?P<argstr>.*)$','satori.client.web.main.loadPOST'),
	(r'^(?P<argstr>.*);(?P<path>.*)$', 'satori.client.web.main.load'),
    (r'^(?P<argstr>.*);(?P<path>.*)$', 'satori.client.web.main.load'),
    (r'^(?P<argstr>.*)$', 'satori.client.web.main.load')
     
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
