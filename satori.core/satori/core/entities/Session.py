# vim:ts=4:sts=4:sw=4:expandtab

import base64
import pickle
from datetime import datetime, timedelta
from django.db import models

class Session(models.Model):

    data            = models.TextField(null=True)
    deadline        = models.DateTimeField()
    first_activity  = models.DateTimeField()
    last_activity   = models.DateTimeField()
    role            = models.ForeignKey('Role', related_name='sessions', null=True)
    auth            = models.CharField(max_length=16, null=True)

    cas_ticket = models.CharField(max_length=64, null=True)

    TIMEOUT = timedelta(minutes = 50)

    @property
    def user(self):
        role = self.role
        if role is None:
            return role
        try:
            from satori.core.models import User
            return User.objects.get(id=role.id)
        except User.DoesNotExist:
            return None
    @property
    def machine(self):
        role = self.role
        if role is None:
            return role
        try:
            from satori.core.models import Machine
            return Machine.objects.get(id=role.id)
        except Machine.DoesNotExist:
            return None

    @staticmethod
    def cleanup():
        Session.objects.filter(deadline_lt=datetime.now())

    @staticmethod
    def start():
        if token_container.token.session is None:
            token_container.token.session = Session()
            token_container.token.session.save()
        return token_container.token.session

    def save(self):
        if self.deadline is None:
            self.deadline = datetime.now() + self.TIMEOUT
        if self.first_activity is None:
            self.first_activity = datetime.now()
        self.last_activity = datetime.now()
        return super(Session, self).save()

    def renew(self):
        if datetime.now() + self.TIMEOUT > self.deadline:
            self.deadline = datetime.now() + self.TIMEOUT

    def login(self, role, auth):
        self.role = role
        self.auth = auth
        self.renew()
        self.save()
        from satori.core.models import OpenIdentity
        from satori.core.models import CentralAuthenticationService
        OpenIdentity.handle_login(self)
        CentralAuthenticationService.handle_login(self)

    def logout(self):
        self.role = None
        self.auth = None
        self.save()
        ret = []
        from satori.core.models import OpenIdentity
        from satori.core.models import CentralAuthenticationService
        r = OpenIdentity.handle_logout(self)
        if r:
            ret.append(r)
        r = CentralAuthenticationService.handle_logout(self)
        if r:
            ret.append(r)
        return ret

    def _get_data_pickle(self):
        if self.data is None:
            return None
        return pickle.loads(base64.urlsafe_b64decode(str(self.data)))
    def _set_data_pickle(self, data):
        if data is None:
            self.data = None
        else:
            self.data = str(base64.urlsafe_b64encode(str(pickle.dumps(data))))
    data_pickle = property(_get_data_pickle, _set_data_pickle)
