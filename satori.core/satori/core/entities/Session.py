# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from datetime import datetime, timedelta
from django.db import models

class Session(models.Model):

    __module__ = "satori.core.models"

    data     = models.TextField()
    deleteOn = models.DateTimeField()

    HOURS = 6

    def save(self, *args, **kwargs):
        self.deleteOn = datetime.now() + timedelta(hours = Session.HOURS)
        ret = super(Session, self).save(*args, **kwargs)
        Session.objects.filter(deleteOn__lt = datetime.now()).delete()
        return ret
