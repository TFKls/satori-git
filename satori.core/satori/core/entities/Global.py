# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.core.dbev import Events

from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class Global(Entity):
    """Model. Special Global object for privileges.
    """

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

    _instance = None

    @ExportMethod(DjangoStruct('Global'), [], PCPermit())
    @staticmethod
    def get_instance():
        if not Global._instance:
            Global._instance = Global.objects.get(guardian=1)
        return Global._instance

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

    @classmethod
    def inherit_rights(cls):
        inherits = super(Global, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE_PRIVILEGES', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'MANAGE_CONTESTS', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'MANAGE_PROBLEMS', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'JUDGE', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'RAW_BLOB', 'id', 'ADMIN')
        return inherits

class GlobalEvents(Events):
    model = Global
    on_insert = on_update = on_delete = []

