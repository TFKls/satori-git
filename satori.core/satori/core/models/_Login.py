# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

import crypt
import random
import string

class Login(Object):

    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_login')

    namespace = models.CharField(max_length=64, default='')
    login     = models.CharField(max_length=64)
    password  = models.CharField(max_length=128)
    user      = models.ForeignKey('User', related_name='authorized_logins')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('namespace', 'login'),)

    def set_password(self, password):
        chars = string.letters + string.digits
        salt = random.choice(chars) + random.choice(chars)
        password = crypt.crypt(password, salt)

    def check_password(self, password):
        return crypt.crypt(password, self.password) == self.password

    def change_password(self, old_password, new_password):
        if self.check_password(old_password):
        	set_password(new_password)

class LoginEvents(events.Events):
    model = Login
    on_insert = on_update = ['login', 'user']
    on_delete = []
