# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Entity import Entity
from satori.core.models._AttributeGroup import AttributeGroup

class Problem(Entity):
    """Model. Description of an (abstract) problems.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_problem')

    name        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")
    statement = models.TextField(blank=True, default="")
    default_test_data = models.OneToOneField('AttributeGroup', related_name='group_problem_defaulttestdata')

    def save(self):
        try:
            x = self.default_test_data
        except AttributeGroup.DoesNotExist:
            default_test_data = AttributeGroup()
            default_test_data.save()
            self.default_test_data = default_test_data

        super(Problem, self).save()

    def __str__(self):
        return self.name+" ("+self.description+")"

    def inherit_right(self, right):
        right = str(right)
        ret = super(Problem, self).inherit_right(right)
        if right == 'EDIT':
            pass
        return ret


class ProblemEvents(Events):
    model = Problem
    on_insert = on_update = ['name']
    on_delete = []

