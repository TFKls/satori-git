# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Object import Object
from satori.core.models._AttributeGroup import AttributeGroup

class ProblemMapping(Object):
    """Model. Intermediary for many-to-many relationship between Contests and
    ProblemIncarnations.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_problemmapping')

    contest     = models.ForeignKey('Contest')
    problem     = models.ForeignKey('Problem')
    code        = models.CharField(max_length=10)
    title       = models.CharField(max_length=64)
    statement   = models.OneToOneField('AttributeGroup', related_name='group_problemmapping_statement')
    default_test_suite = models.ForeignKey('TestSuite')

    def save(self):
        try:
            x = self.statement
        except AttributeGroup.DoesNotExist:
            statement = AttributeGroup()
            statement.save()
            self.statement = statement

        super(ProblemMapping, self).save()
    
    def __str__(self):
        return self.code+": "+self.title+ " ("+self.contest.name+","+self.problem.name+")"

    def inherit_right(self, right):
        right = str(right)
        ret = super(ProblemMapping, self).inherit_right(right)
        if right == 'VIEW':
        	ret.append((self.contest,'VIEWTASKS'))
        if right == 'EDIT':
            ret.append((self.contest,'MANAGE'))
        if right == 'SUBMIT':
            ret.append((self.contest,'SUBMIT'))
        return ret
    

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'code'), ('contest', 'problem'))

class ProblemMappingEvents(Events):
    model = ProblemMapping
    on_insert = on_update = ['contest', 'problem']
    on_delete = []

