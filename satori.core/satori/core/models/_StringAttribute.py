# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._OpenAttribute import OpenAttribute

class StringAttribute(OpenAttribute):
    """Model. Open attribute of kind "string".
    """
    __module__ = "satori.core.models"

    value       = models.CharField(max_length=50)

