# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

class Notification(models.Model):

    __module__ = "satori.core.models"

    action      = models.CharField(max_length=1)
    table       = models.CharField(max_length=50)
    object      = models.IntegerField()
    transaction = models.IntegerField()
    previous    = models.IntegerField(null=True)
    user        = models.IntegerField(null=True)