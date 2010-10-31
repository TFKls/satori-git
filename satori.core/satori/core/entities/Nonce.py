# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

class Nonce(models.Model):

    __module__ = "satori.core.models"

    server_url = models.CharField(max_length=2048)
    timestamp  = models.IntegerField()
    salt       = models.CharField(max_length=64)

    class Meta:
        unique_together = (('server_url', 'timestamp', 'salt'),)