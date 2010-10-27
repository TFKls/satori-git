# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

class OpenAttribute(models.Model):
    """Model. Base for all kinds of open attributes.
    """
    __module__ = "satori.core.models"

    object      = models.ForeignKey('Entity', related_name='attributes')
    name        = models.CharField(max_length=50)
    is_blob     = models.BooleanField()
    value       = models.TextField()
    filename    = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        if not self.is_blob:
            self.filename = ''
        super(OpenAttribute, self).save(*args, **kwargs)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('object', 'name'),)

class OpenAttributeEvents(Events):
    model = OpenAttribute
    on_insert = on_update = on_delete = []
