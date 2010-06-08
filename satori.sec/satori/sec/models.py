# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

class Nonce(models.Model):

    __module__ = "satori.sec.models"

    server_url = models.CharField(max_length=2047)
    timestamp  = models.IntegerField()
    salt       = models.CharField(max_length=40)

    class Meta:
        unique_together = (('server_url', 'timestamp', 'salt'),)

class Association(models.Model):

    __module__ = "satori.sec.models"

    server_url = models.CharField(max_length=2047)
    handle     = models.CharField(max_length=255)
    secret     = models.CharField(max_length=511)
    issued     = models.IntegerField()
    lifetime   = models.IntegerField()
    assoc_type = models.CharField(max_length=64)

    class Meta:
        unique_together = (('server_url', 'handle'),)
