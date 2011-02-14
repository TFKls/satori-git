# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Global(Entity):
    """Model. Special Global object for privileges.
    """
    guardian         = models.IntegerField(unique=True)

    anonymous        = models.ForeignKey('Role', related_name='+')
    authenticated    = models.ForeignKey('Role', related_name='+')
    zero             = models.ForeignKey('Role', related_name='+')

    assignment       = models.ForeignKey('Problem', related_name='+')

    profile_fields   = models.TextField(blank=True, default="")

    judges           = AttributeGroupField(PCOr(PCArg('self', 'ADMIN'), PCArg('', 'MANAGE_PROBLEMS')), PCArg('self', 'ADMIN'), '')
    generators       = AttributeGroupField(PCArg('self', 'ADMIN'), PCArg('self', 'ADMIN'), '')

    class ExportMeta(object):
        fields = [('anonymous', 'VIEW'), ('authenticated', 'VIEW'), ('zero', 'VIEW'), ('assignment', 'VIEW'), ('profile_fields', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Global, cls).inherit_rights()
        cls._inherit_add(inherits, 'TEMPORARY_SUBMIT', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'MANAGE_PRIVILEGES', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'MANAGE_CONTESTS', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'MANAGE_PROBLEMS', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'JUDGE', 'id', 'ADMIN')
        cls._inherit_add(inherits, 'RAW_BLOB', 'id', 'JUDGE')
        return inherits

    def save(self, *args, **kwargs):
        self.guardian = 1

        self.fixup_judges()
        self.fixup_generators()

        super(Global, self).save(*args, **kwargs)

    @staticmethod
    def create():
        zero = Role(name='ZERO')
        zero.save()

        authenticated = Role(name='AUTHENTICATED')
        authenticated.save()

        anonymous = Role(name='ANONYMOUS')
        anonymous.save()

        anonymous.add_member(authenticated)

        assignment = Problem(name='ASSIGNMENT', description='Dummy problem for assignments')
        assignment.save()
        assignment_suite = TestSuite(problem=assignment, name='ASSIGNMENT', description='Dummy test suite for assignments', dispatcher='SerialDispatcher', reporter='AssignmentReporter', accumulators='')
        assignment_suite.save()

        Privilege.grant(anonymous, authenticated, 'VIEW')
        Privilege.grant(anonymous, anonymous, 'VIEW')
        Privilege.grant(anonymous, zero, 'VIEW')
        Privilege.grant(anonymous, assignment, 'VIEW')

        g = Global()
        g.zero = zero
        g.authenticated = authenticated
        g.anonymous = anonymous
        g.assignment = assignment
        g.save()
        Privilege.grant(authenticated, g, 'VIEW')

        return g        

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

    @ExportMethod(TypedMap(unicode, unicode), [], PCPermit())
    @staticmethod
    def get_reporters():
        from satori.core.checking.reporters import reporters
        ret = {}
        for name in reporters:
            ret[name] = reporters[name].__doc__
            if ret[name] is None:
                ret[name] = ''
        return ret

    @ExportMethod(TypedMap(unicode, unicode), [], PCPermit())
    @staticmethod
    def get_aggregators():
        from satori.core.checking.aggregators import aggregators
        ret = {}
        for name in aggregators:
            ret[name] = aggregators[name].__doc__
            if ret[name] is None:
                ret[name] = ''
        return ret

class GlobalEvents(Events):
    model = Global
    on_insert = on_update = on_delete = []
