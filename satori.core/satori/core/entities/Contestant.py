# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Role

@ExportModel
class Contestant(Role):
    """Model. A Role for a contest participant.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_contestant')

    usernames  = models.CharField(max_length=200)
    contest    = models.ForeignKey('Contest', related_name='contestants')
    accepted   = models.BooleanField(default=False)
    invisible  = models.BooleanField(default=False)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('accepted', 'VIEW'), ('invisible', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Contestant, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW')
        cls._inherit_add(inherits, 'MANAGE', 'contest', 'MANAGE')
        cls._inherit_add(inherits, 'OBSERVE', 'contest', 'OBSERVE')
        return inherits
    
    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contestant'), bool], PCArg('self', 'MANAGE'))
    def set_accepted(self, accepted):
        self.accepted = accepted
        self.save()
        if accepted:
            self.contest.contestant_role.add_member(self)
        else:
            self.contest.contestant_role.delete_member(self)
        return self

    def update_usernames(self):
        name = ', '.join(x.name for x in self.get_member_users())
        if len(name) > 200:
            name = name[0:197] + '...'
        self.usernames = name;
        self.save()
        return self #TODO: Poinformowac przeliczanie rankingow

    @ExportMethod(DjangoStructList('User'), [DjangoId('Contestant')], PCArg('self', 'VIEW'))
    def get_member_users(self):
        return User.objects.filter(parents=self)

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contestant'), bool], PCArg('self', 'MANAGE'))
    def set_invisible(self, invisible):
        self.invisible = invisible
        self.save()
        return self #TODO: Poinformowac przeliczanie rankingow

class ContestantEvents(Events):
    model = Contestant
    on_insert = on_update = ['name', 'contest']
    on_delete = []
