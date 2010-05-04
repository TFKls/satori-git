from django.db import models
from satori.dbev import events
from satori.ars import django2ars
from satori.core.models._OpenAttribute import OpenAttribute

class StringAttribute(OpenAttribute):
    """Model. Open attribute of kind "string".
    """
    __module__ = "satori.core.models"

    value       = models.CharField(max_length=50)

