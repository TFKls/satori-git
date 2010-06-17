from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._OpenAttribute import OpenAttribute

class OpaqueAttribute(OpenAttribute):
    """Model. Open attribute of kind "opaque".
    """
    __module__ = "satori.core.models"

    value       = models.TextField()

