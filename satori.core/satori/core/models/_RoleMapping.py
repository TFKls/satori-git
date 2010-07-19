from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object

class RoleMapping(Object):
    """Model. Intermediary for many-to-many relationship between Roles.
    """
    __module__ = "satori.core.models"

    parent     = models.ForeignKey('Role', related_name='childmap')
    child      = models.ForeignKey('Role', related_name='parentmap')
    title      = models.CharField(max_length=64)
    
    def __unicode__(self):
        return self.title+ " ("+self.child.name+","+self.parent.name+")"

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('parent', 'child'),)

class RoleMappingEvents(events.Events):
    model = RoleMapping
    on_insert = on_update = ['parent', 'child']
    on_delete = []

class RoleMappingOpers(django_.Opers):
    rolemapping = django_.ModelProceduresProvider(RoleMapping)

