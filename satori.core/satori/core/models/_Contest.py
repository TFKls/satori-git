# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Entity import Entity
from satori.core.models._AttributeGroup import AttributeGroup

class Contest(Entity):
    """Model. Description of a contest.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_contest')

    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('Problem', through='ProblemMapping')
    files       = models.OneToOneField('AttributeGroup', related_name='group_contest_files')
    contestant_role = models.ForeignKey('Role')

    def save(self):
        try:
            x = self.files
        except AttributeGroup.DoesNotExist:
            files = AttributeGroup()
            files.save()
            self.files = files

        super(Contest, self).save()

    def __str__(self):
        return self.name
    # TODO: add presentation options

    def inherit_right(self, right):
        right = str(right)
        ret = super(Contest, self).inherit_right(right)
        if right == 'VIEW' or right == 'OBSERVE' or right == 'VIEWTASKS':
            ret.append((self,'MANAGE'))
        if right == 'APPLY':
            ret.append((self,'JOIN'))
        return ret



class ContestEvents(Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

