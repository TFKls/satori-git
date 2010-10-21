# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

class Association(models.Model):

    __module__ = "satori.core.models"

    server_url = models.CharField(max_length=2048)
    handle     = models.CharField(max_length=256)
    secret     = models.CharField(max_length=512)
    issued     = models.IntegerField()
    lifetime   = models.IntegerField()
    assoc_type = models.CharField(max_length=64)

    class Meta:
        unique_together = (('server_url', 'handle'),)
