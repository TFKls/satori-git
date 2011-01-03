# vim:ts=4:sts=4:sw=4:expandtab

import crypt
import random
import string
import ipaddr

from satori.ars.server  import server_info
from satori.core.dbev   import Events
from satori.core.models import Role
from satori.core.models import LoginFailed

@ExportModel
class Machine(Role):
    """Model. A Machine.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_machine')

    login       = models.CharField(max_length=64, unique=True)
    secret      = models.CharField(max_length=128)
    address     = models.IPAddressField()
    netmask     = models.IPAddressField(default='255.255.255.255')

    class ExportMeta(object):
        fields = [('login', 'VIEW'), ('address', 'VIEW'), ('netmask', 'VIEW')]

    @ExportMethod(DjangoStruct('Machine'), [unicode, unicode, unicode, unicode, unicode], PCGlobal('ADMIN'))
    @staticmethod
    def register(login, name, secret, address, netmask):
        machine = Machine(login=login, name=name, address=address, netmask=netmask)
        machine.set_secret(secret)
        machine.save()
        Privilege.grant(token_container.token.role, machine, 'MANAGE')
        return machine

    @ExportMethod(unicode, [unicode, unicode], PCPermit())
    @staticmethod
    def authenticate(login, secret):
        try:
            machine = Machine.objects.get(login=login)
        except Machine.DoesNotExist:
            raise LoginFailed()
        if not machine.check_ip(server_info.client_ip):
            raise LoginFailed()
        if not machine.check_secret(secret):
            raise LoginFailed()
        session = Session.start()
        session.login(machine, 'machine')
        return str(token_container.token)

    @ExportMethod(DjangoStruct('Machine'), [DjangoId('Machine'), unicode], PCArg('self', 'MANAGE'))
    def set_secret(self, secret):
        chars = string.letters + string.digits
        salt = random.choice(chars) + random.choice(chars)
        self.secret = crypt.crypt(secret, salt)
        return self

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
