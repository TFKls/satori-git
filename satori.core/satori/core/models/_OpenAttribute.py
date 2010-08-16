# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models.modules import OATYPES

class OpenAttribute(models.Model):
    """Model. Base for all kinds of open attributes.
    """
    __module__ = "satori.core.models"

    object      = models.ForeignKey('Object', related_name='attributes')
    name        = models.CharField(max_length=50)

    oatype       = models.CharField(max_length=16, choices=OATYPES)
    string_value = models.CharField(max_length=50)
    opaque_value = models.TextField()
    blob_hash    = models.ForeignKey('Blob')

    def save(self, *args, **kwargs):
        str = self.string_value
        opa = self.opaque_value
        blo = self.blob_hash
        self.string_value = None
        self.opaque_value = None
        self.blob_hash = None
        if self.oatype == 'string':
        	self.string_value = str
        if self.oatype == 'opaque':
        	self.opaque_value = opa
        if self.oatype == 'blob':
        	self.blob_hash = blo
        super(OpenAttribute, self).save(*args, **kwargs)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('object', 'name'),)

class OpenAttributeEvents(events.Events):
    model = OpenAttribute
    on_insert = on_update = on_delete = []
