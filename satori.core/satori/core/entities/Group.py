# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Role

@ExportModel
class Group(Role):
    """Model. A Role which can contain other roles.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_group')

    class ExportMeta(object):
        pass


class GroupEvents(Events):
    model = Group
    on_insert = on_update = on_delete = []
