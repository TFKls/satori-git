# vim:ts=4:sts=4:sw=4:expandtab

from django.core.exceptions import ValidationError
from django.db import models

from satori.core.dbev import Events

def validate_filename(value):
    try:
        value.decode('ascii')
    except:
        raise ValidationError(u'filename \'%s\' contains invalid characters' % value)
    for l in value:
        if not (l.isalpha() or l.isdigit() or l == '_' or l == '-' or l == "."):
            raise ValidationError(u'filename \'%s\' contains invalid characters' % value)

class OpenAttribute(models.Model):
    """Model. Base for all kinds of open attributes.
    """
    entity   = models.ForeignKey('Entity', related_name='attributes', on_delete=models.CASCADE)
    name     = models.CharField(max_length=64)
    is_blob  = models.BooleanField()
    value    = models.TextField(blank=True)
    filename = models.CharField(max_length=64, blank=True, validators=[validate_filename])

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('entity', 'name'),)

    def save(self, *args, **kwargs):
        if not self.is_blob:
            self.filename = ''
        self.full_clean()
        super(OpenAttribute, self).save(*args, **kwargs)

class OpenAttributeEvents(Events):
    model = OpenAttribute
    on_insert = on_update = on_delete = []
