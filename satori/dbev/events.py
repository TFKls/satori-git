# vim:ts=4:sts=4:sw=4:expandtab
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import models
import satori.dbev.models
from satori.dbev import versions

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
        versions.Versions(model, events)

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
