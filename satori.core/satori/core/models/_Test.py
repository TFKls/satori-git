# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Entity import Entity
from satori.core.models._AttributeGroup import AttributeGroup

class Test(Entity):
    """Model. Single test.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_test')

    problem     = models.ForeignKey('Problem')
    name        = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")
    environment = models.CharField(max_length=50)
    data    = models.OneToOneField('AttributeGroup', related_name='group_test_data')
    obsolete = models.BooleanField(default=False)

    def save(self):
        try:
            x = self.data
        except AttributeGroup.DoesNotExist:
            data = AttributeGroup()
            data.save()
            self.data = data

        super(Test, self).save()

    def inherit_right(self, right):
        right = str(right)
        ret = super(Test, self).inherit_right(right)
        if right == 'EDIT':
            ret.append((self.problem,'EDIT'))
        return ret


    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

class TestEvents(Events):
    model = Test
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []

