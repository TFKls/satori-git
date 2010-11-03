# vim:ts=4:sts=4:sw=4:expandtab
#! module models

import crypt
import random
import string
import ipaddr

from satori.core.export        import ExportMethod, token_container
from satori.core.export_django import ExportModel
from satori.core.dbev               import Events

from satori.core.models import Role

@ExportModel
class Machine(Role):
    """Model. A Machine.
    """

    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_machine')

    secret  = models.CharField(max_length=128)
    address = models.IPAddressField()
    netmask = models.IPAddressField(default='255.255.255.255')

    class ExportMeta(object):
        fields = [('address', 'VIEW'), ('netmask', 'VIEW'), ('secret', 'MANAGE')]

    @ExportMethod(DjangoStruct('Machine'), [unicode, unicode, unicode, unicode], PCGlobal('ADMIN'))
    @staticmethod
    def register(name, secret, address, netmask):
        machine = Machine(name=name, address=address, netmask=netmask)
        machine.set_secret(secret)
        machine.save()
        if token_container.token.user:
            Privilege.grant(token_container.token.user, machine, 'MANAGE')
        return machine

    @ExportMethod(unicode, [unicode], PCPermit())
    @staticmethod
    def authenticate(secret):
        for machine in Machine.objects.all():
            if machine.check_ip(server_info.client_ip) and machine.check_secret(secret):
                return str(Token(user=machine, auth='machine', validity=timedelta(hours=24)))

    @ExportMethod(NoneType, [DjangoId('Machine'), unicode], PCArg('self', 'MANAGE'))
    def set_secret(self, secret):
        chars = string.letters + string.digits
        salt = random.choice(chars) + random.choice(chars)
        self.secret = crypt.crypt(secret, salt)

    @ExportMethod(bool, [DjangoId('Machine'), unicode], PCArg('self', 'MANAGE'))
    def check_secret(self, secret):
        return crypt.crypt(secret, self.secret) == self.secret

    @ExportMethod(NoneType, [DjangoId('Machine'), unicode], PCArg('self', 'MANAGE'))
    def check_ip(self, ip):
        net = ipaddr.IPv4Network(self.address + '/' + self.netmask)
        addr = ipaddr.IPv4Address(ip)
        return addr in net

class MachineEvents(Events):
    model = Machine
    on_insert = on_update = on_delete = []
    
