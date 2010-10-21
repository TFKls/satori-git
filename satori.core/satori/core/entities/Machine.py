# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import User

import crypt
import random
import string
import ipaddr

class Machine(User):
    """Model. A Machine.
    """
    __module__ = "satori.core.models"
    parent_user = models.OneToOneField(User, parent_link=True, related_name='cast_machine')

    secret  = models.CharField(max_length=128)
    address = models.IPAddressField()
    netmask = models.IPAddressField(default='255.255.255.255')

    def set_secret(self, secret):
        chars = string.letters + string.digits
        salt = random.choice(chars) + random.choice(chars)
        self.secret = crypt.crypt(secret, salt)

    def check_secret(self, secret):
        return crypt.crypt(secret, self.secret) == self.secret

    def check_ip(self, ip):
        net = ipaddr.IPv4Network(self.address + '/' + self.netmask)
        addr = ipaddr.IPv4Address(ip)
        return addr in net

class MachineEvents(Events):
    model = Machine
    on_insert = on_update = on_delete = []
#! module api

from satori.ars.wrapper import WrapperClass
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Machine

class ApiMachine(WrapperClass):
    machine = ModelWrapper(Machine)

