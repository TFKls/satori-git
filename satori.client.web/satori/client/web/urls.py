from django.conf.urls.defaults import *
from satori.core.models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
#     (r'^$', 'satoritest.main.loaddefault'),
	(r'^create/','satoritest.createdata.create'),
	(r'^admin/', include(admin.site.urls)),
	(r'^files/(?P<path>.*)/$', 'django.views.static.serve',
        {'document_root': 'files/'}),        
	(r'^files/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'files/'}),
	(r'^process/(?P<argstr>.*)/$','satoritest.main.loadPOST'),
	(r'^process/(?P<argstr>.*)$','satoritest.main.loadPOST'),
	(r'^(?P<argstr>.*)/(?P<path>.*)/$', 'satoritest.main.load'),
    (r'^(?P<argstr>.*)/(?P<path>.*)$', 'satoritest.main.load'),
    (r'^(?P<argstr>.*)$', 'satoritest.main.load')
     
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
