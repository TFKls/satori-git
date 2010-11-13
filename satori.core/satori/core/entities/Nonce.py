# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

class Nonce(models.Model):


    server_url = models.CharField(max_length=2048)
    timestamp  = models.IntegerField()
    salt       = models.CharField(max_length=64)

    class Meta:
        unique_together = (('server_url', 'timestamp', 'salt'),)
