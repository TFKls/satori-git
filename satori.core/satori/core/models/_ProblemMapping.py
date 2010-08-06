# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

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
    statement   = models.TextField(blank=True, default="")
    default_test_suite = models.ForeignKey('TestSuite')
    
    def __unicode__(self):
        return self.code+": "+self.title+ " ("+self.contest.name+","+self.problem.name+")"

    def inherit_right(self, right):
        right = str(right)
        ret = list()
        if right == 'EDIT':
            ret.append((self.contest,'MANAGE'))
        return ret
    

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'code'), ('contest', 'problem'))

class ProblemMappingEvents(events.Events):
    model = ProblemMapping
    on_insert = on_update = ['contest', 'problem']
    on_delete = []

