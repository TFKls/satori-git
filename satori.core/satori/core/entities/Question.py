# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Question(Entity):
    """Model. Description of a question.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_question')

    problem       = models.ForeignKey('ProblemMapping', null=True)
    contest       = models.ForeignKey('Contest')
    content       = models.TextField(blank=True)
    answer        = models.TextField(blank=True, null=True)
    date_created  = models.DateTimeField(auto_now_add=True)

    class ExportMeta(object):
        fields = [('problem', 'VIEW'), ('contest', 'VIEW'), ('content', 'VIEW'), ('answer', 'VIEW'), ('date_created', 'VIEW')]

class QuestionEvents(Events):
    model = Question
    on_insert = on_update = ['topic', 'time']
    on_delete = []
