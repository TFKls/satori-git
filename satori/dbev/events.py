import select
import psycopg2.extensions
from django.db import models
from django.db import connection
import versions

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class EventsRegistry(object):
    """
    Registry of Events classes.
    """
    def __init__(self):
        self._registry = {}

    def register(self, model, events):
        if model in self._registry:
            raise AlreadyRegistered('The model %s is already registered' % model.__name__)
        self._registry[model] = events(self)
        v = versions.Versions(model, events)

    def sql(self):
        for model, events in self._registry.iteritems():
            print model._meta.app_label, model._meta.module_name, events.on_insert, events.on_update, events.on_delete

registry = EventsRegistry()

class EventsBase(type):
    """
    Metaclass for Events.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(EventsBase, cls).__new__
        parents = [b for b in bases if isinstance(b, EventsBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)
        registry.register(attrs.pop('model'), super_new(cls, name, bases, attrs)) 

class Events(object):
    """
    Options for automatic event generation on database change of ``model`` instances.
    """
    __metaclass__ = EventsBase
    model = None
    on_insert = None
    on_update = None
    on_delete = None
    versions = True

    def __init__(self, registry):
        self.registry = registry
        super(Events, self).__init__()

class EventsListener(object):
    """
    Listens to Notify events.
    """
    def __init__(self):
        notification = models.get_model('dbev','notification')
        cursor = connection.cursor()
        con = connection.connection
        con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        con.commit()
        cursor = con.cursor()
        cursor.execute('LISTEN '+notification.notification+';')
        print "Waiting for 'NOTIFY "+notification.notification+"'"
        while 1:
            if select.select([cursor],[],[],5)==([],[],[]):
                print "Timeout"
            else:
                if cursor.isready():
                    print "Got NOTIFY:", cursor.connection.notifies.pop()
