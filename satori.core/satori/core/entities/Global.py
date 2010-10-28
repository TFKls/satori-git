# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.core.dbev import Events

from satori.core.export        import ExportMethod, TypedMap, PCPermit
from satori.core.export_django import ExportModel, generate_attribute_group
from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class Global(Entity):
    """Model. Special Global object for privileges.
    """
    __module__ = "satori.core.models"

    guardian = models.IntegerField(unique=True)

    anonymous = models.ForeignKey('Role', related_name='global_anonymous+')
    authenticated = models.ForeignKey('Role', related_name='global_authenticated+')

    generate_attribute_group('Global', 'checkers', 'ADMIN', 'ADMIN', globals(), locals())
    generate_attribute_group('Global', 'generators', 'ADMIN', 'ADMIN', globals(), locals())

    def save(self):
        self.guardian = 1

        self.fixup_checkers()
        self.fixup_generators()

        try:
            x = self.authenticated
        except Role.DoesNotExist:
            authenticated = Role(name='AUTHENTICATED')
            authenticated.save()
            self.authenticated = authenticated

        try:
            x = self.anonymous
        except Role.DoesNotExist:
            anonymous = Role(name='ANONYMOUS')
            anonymous.save()
            self.anonymous = anonymous

        super(Global, self).save()

    _instance = None;
    @ExportMethod(DjangoStruct('Global'), [], PCPermit())
    @staticmethod
    def get_instance():
        if Global._instance:
        	return Global._instance
        try:
            g = Global.objects.get(guardian=1)
        except:
            g = Global()
            g.save()
        Global._instance = g
        return g

    @ExportMethod(TypedMap(unicode, unicode), [], PCPermit())
    @staticmethod
    def get_accumulators():
        from satori.core.checking.accumulators import accumulators
        ret = {}
        for name in accumulators:
            ret[name] = accumulators[name].__doc__
            if ret[name] is None:
                ret[name] = ''
        return ret

    @ExportMethod(TypedMap(unicode, unicode), [], PCPermit())
    @staticmethod
    def get_dispatchers():
        from satori.core.checking.dispatchers import dispatchers
        ret = {}
        for name in dispatchers:
            ret[name] = dispatchers[name].__doc__
            if ret[name] is None:
                ret[name] = ''
        return ret


class GlobalEvents(Events):
    model = Global
    on_insert = on_update = on_delete = []

