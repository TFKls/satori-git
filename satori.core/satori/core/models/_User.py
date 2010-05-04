from django.db import models
from satori.dbev import events
from satori.ars import django2ars
from satori.core.models._Role import Role

class User(Role):
    """Model. A Role which can be logged onto.
    """
    __module__ = "satori.core.models"

    pass
    # add validation
class UserEvents(events.Events):
    model = User
    on_insert = on_update = ['name']
    on_delete = []
