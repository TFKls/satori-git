from django.db import models
from satori.dbev import events
from satori.ars import django2ars
from satori.core.models._Role import Role

class Contestant(Role):
    """Model. A Role for a contest participant.
    """
    __module__ = "satori.core.models"

    contest     = models.ForeignKey('Contest')
class ContestantEvents(events.Events):
    model = Contestant
    on_insert = on_update = ['name', 'contest']
    on_delete = []
