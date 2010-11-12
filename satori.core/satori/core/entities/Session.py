# vim:ts=4:sts=4:sw=4:expandtab
#! module models

import base64
import pickle
from datetime import datetime, timedelta
from django.db import models

class Session(models.Model):

    __module__ = "satori.core.models"

    data     = models.TextField()
    deleteOn = models.DateTimeField()

    HOURS = 6

    def save(self):
        self.deleteOn = datetime.now() + timedelta(hours = Session.HOURS)
        return super(Session, self).save()

    def _get_data_pickle(self):
        return pickle.loads(base64.urlsafe_b64decode(str(self.data)))
    def _set_data_pickle(self, data):
        self.data = str(base64.urlsafe_b64encode(str(pickle.dumps(data))))
    data_pickle = property(_get_data_pickle, _set_data_pickle)
