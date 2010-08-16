# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events

OATYPES_STRING = 1
OATYPES_BLOB = 2

OATYPES = (
    (OATYPES_STRING, 'String Attribute'),
    (OATYPES_BLOB, 'Blob Attribute'),
)

class OpenAttribute(models.Model):
    """Model. Base for all kinds of open attributes.
    """
    __module__ = "satori.core.models"

    object      = models.ForeignKey('Object', related_name='attributes')
    name        = models.CharField(max_length=50)

    oatype       = models.IntegerField(choices=OATYPES)
    string_value = models.TextField()
    blob_hash    = models.ForeignKey('Blob')

    def save(self, *args, **kwargs):
        str = self.string_value
        blo = self.blob_hash
        self.string_value = None
        self.blob_hash = None
        if self.oatype == OATYPES_STRING:
        	self.string_value = str
        if self.oatype == OATYPES_BLOB:
        	self.blob_hash = blo
        super(OpenAttribute, self).save(*args, **kwargs)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('object', 'name'),)

class OpenAttributeEvents(events.Events):
    model = OpenAttribute
    on_insert = on_update = on_delete = []
