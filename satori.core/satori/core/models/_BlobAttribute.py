from django.db import models
from satori.dbev import events
from satori.core.models._OpenAttribute import OpenAttribute

class BlobAttribute(OpenAttribute):
    """Model. Open attribute of kind "blob".
    """
    __module__ = "satori.core.models"

    hash        = models.ForeignKey('Blob')
    
