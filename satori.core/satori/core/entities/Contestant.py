# vim:ts=4:sts=4:sw=4:expandtab

#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel
from satori.core.dbev               import Events

from satori.core.models import Role

@ExportModel
class Contestant(Role):
    """Model. A Role for a contest participant.
    """
    __module__ = "satori.core.models"
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_contestant')

    contest    = models.ForeignKey('Contest')
    accepted   = models.BooleanField(default=False)
    invisible  = models.BooleanField(default=False)

    @classmethod
    def inherit_rights(cls):
        inherits = super(Contestant, cls).inherit_rights()
        for key in inherits.keys():
            cls._inherit_add(inherits, key, 'contest', key)
        cls._inherit_add(inherits, 'OBSERVE', 'contest', 'OBSERVE')
        return inherits

    @ExportMethod(unicode, [DjangoId('Contestant')], PCArg('self', 'VIEW'))
    def name_auto(self):
        return ','.join(x.fullname for x in self.get_members())

    @ExportMethod(DjangoStructList('User'), [DjangoId('Contestant')], PCArg('self', 'VIEW'))
    def get_member_users(self):
        return User.objects.filter(parents=self)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('accepted', 'VIEW'), ('invisible', 'VIEW')]

class ContestantEvents(Events):
    model = Contestant
    on_insert = on_update = ['name', 'contest']
    on_delete = []

