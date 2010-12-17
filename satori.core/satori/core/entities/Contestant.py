# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev               import Events

from satori.core.models import Role

@ExportModel
class Contestant(Role):
    """Model. A Role for a contest participant.
    """
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
    
    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contestant'), bool], PCArg('self', 'MANAGE'))
    def set_accepted(self, accepted):
        self.accepted = accepted
        self.save()

        if accepted:
            self.contest.contestant_role.add_member(self)
        else:
            self.contest.contestant_role.delete_member(self)

        return self

    @ExportMethod(unicode, [DjangoId('Contestant')], PCArg('self', 'VIEW'))
    def name_auto(self):
        name = ','.join(x.name for x in self.get_member_users())
        cname = self.contest.name + ': ' + name;
        if cname != self.name:
            self.name = cname;
            self.save()
        return name

    @ExportMethod(DjangoStructList('User'), [DjangoId('Contestant')], PCArg('self', 'VIEW'))
    def get_member_users(self):
        return User.objects.filter(parents=self)

    # MANAGE on self
    def set_invisible():
        # update ranking
        # set invisible
        pass

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('accepted', 'VIEW'), ('invisible', 'VIEW')]

class ContestantEvents(Events):
    model = Contestant
    on_insert = on_update = ['name', 'contest']
    on_delete = []
