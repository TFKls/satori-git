# vim:ts=4:sts=4:sw=4:expandtab

import base64
import pickle
from django.db import models

class RawEvent(models.Model):

    transaction = models.IntegerField(null=True)
    data        = models.TextField()
    
    def send(self, event):
        self.data = str(base64.urlsafe_b64encode(str(pickle.dumps(event))))
        self.save()
    def recv(self):
        return pickle.loads(base64.urlsafe_b64decode(str(self.data)))

