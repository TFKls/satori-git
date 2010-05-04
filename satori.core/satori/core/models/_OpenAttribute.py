from django.db import models
from satori.dbev import events
from satori.ars import django2ars
class OpenAttribute(models.Model):
    """Model. Base for all kinds of open attributes.
    """
    __module__ = "satori.core.models"

    object      = models.ForeignKey('Object', related_name='attributes')
    name        = models.CharField(max_length=50)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('object', 'name'),)
