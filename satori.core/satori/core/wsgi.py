import sys
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'satori.core.settings')

application = get_wsgi_application()

# initialize thrift server structures - takes a long time and it's better
# to do it on startup than during the first request
import satori.core.thrift_server

