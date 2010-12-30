# vim:ts=4:sts=4:sw=4:expandtab

import base64
import pickle
from datetime import datetime, timedelta

from django.db import models

ExternalSessionFailed = DefineException('ExternalSessionFailed', 'External session failed', [])

class ExternalSession(models.Model):
    """
    """
    session     = models.ForeignKey('Session', related_name='external_sessions')
    external_id = models.CharField(max_length=64)

    @ExportMethod(datetime, [unicode], PCPermit(), [ExternalSessionFailed])
    @staticmethod
    def last_activity(id):
        try:
            eses = ExternalSession.objects.get(external_id=id)
            return eses.session.last_activity
        except ExternalSession.DoesNotExist:
            raise ExternalSessionFailed

    @ExportMethod(NoneType, [unicode], PCPermit(), [ExternalSessionFailed])
    @staticmethod
    def logout(id):
        pass
