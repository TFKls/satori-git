from django.db import models
from satori.dbev import events
from satori.objects import ReturnValue, Argument
from satori.ars import django_
from satori.ars.model import String
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

class UserOpers(django_.Opers):
    user = django_.ModelProceduresProvider(User)
    
    @user.method
    @ReturnValue(type=User)
    @Argument(name='name', type=str)
    def create(name):
        t = User()
        t.name = name
        t.save()
        return t


