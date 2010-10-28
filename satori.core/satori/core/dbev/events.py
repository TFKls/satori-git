# vim:ts=4:sts=4:sw=4:expandtab

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

registry = {}

class EventsBase(type):
    """
    Metaclass for Events.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(EventsBase, cls).__new__
        parents = [b for b in bases if isinstance(b, EventsBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)
        events = super_new(cls, name, bases, attrs)
        model = attrs.pop('model')
        if model in registry:
            raise AlreadyRegistered('The model %s is already registered' % model.__name__)
        for parent in model._meta.parents.keys():
            if parent not in registry:
                raise NotRegistered('Parent model %s is not registered' % parent.__name__)
        registry[model] = events()
        return events


class Events(object):
    """
    Options for automatic event generation on database change of ``model`` instances.
    """
    __metaclass__ = EventsBase
    model = None
    on_insert = None
    on_update = None
    on_delete = None
