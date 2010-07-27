# vim:ts=4:sts=4:sw=4:expandtab
from django.db import models
from satori.dbev import events
from satori.ars import django_
class Object(models.Model):
    """Model. Base for all database objects. Provides common GUID space.
    """
    __module__ = "satori.core.models"

    model = models.CharField(max_length=64, editable=False)

    def save(self):
        if not self.model:
        	  self.model = self._meta.app_label + '.' + self._meta.object_name
        super(Object, self).save()
  
    def inherit_right(self, right):
        right = str(right)
        ret = list()
        if right == 'VIEW':
        	ret.append((self,'MODERATE'))
        if right == 'MODERATE':
        	ret.append((self,'EDIT'))
        if right != 'ADMIN':
        	  ret.append((self,'ADMIN'))
        return ret

    def demand_right(self, token, right):
        from satori.core.sec import Token, CheckRights
        checker = CheckRights()
        roleset = RoleSet(user=User.objects.get(id=Token(str(token)).user))
        cani = checker.check(roleset, self, str(right))
        if not cani:
        	raise 'Insufficient rights'

    pass
    # attributes    (Manager created automatically by OpenAttribute)

