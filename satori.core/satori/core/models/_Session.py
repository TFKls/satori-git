# vim:ts=4:sts=4:sw=4:expandtab

from datetime import datetime, timedelta
from django.db import models
from satori.core.models._Blob import BlobField

class Session(models.Model):

    __module__ = "satori.core.models"

    data     = BlobField()
    deleteOn = models.DateTimeField(null=True)

    HOURS = 6

    def save(self, *args, **kwargs):
        deleteOn = datetime.now() + timedelta(hours = Session.HOURS)
        super(Session, self).save(*args, **kwargs)
        Session.objects.filter(deleteOn__lt = datetime.now()).delete()
