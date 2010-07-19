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

    def inheritRights(self, right):
        right = str(right)
        ret = list()
        if right != 'ADMIN':
        	  ret.append((self,'ADMIN'))
        return ret

    pass
    # attributes    (Manager created automatically by OpenAttribute)

