# vim:ts=4:sts=4:sw=4:expandtab

import ipaddr

from satori.ars.server  import server_info
from satori.core.dbev   import Events
from satori.core.models import Role, LoginFailed, InvalidLogin, login_ok, password_ok, password_crypt, password_check, password_rehash_old 
from satori.core.models import LoginFailed

@ExportModel
class Machine(Role):
    """Model. A Machine.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_machine')

    login       = models.CharField(max_length=64, unique=True)
    password    = models.CharField(max_length=128, null=True)
    address     = models.IPAddressField()
    netmask     = models.IPAddressField(default='255.255.255.255')

    class ExportMeta(object):
        fields = [('login', 'VIEW'), ('address', 'VIEW'), ('netmask', 'VIEW')]

    def save(self, *args, **kwargs):
        login_ok(self.login)
        if Machine.objects.filter(login=self.login).exclude(id=self.id):
            raise InvalidLogin(login=self.login, reason='is already used')
        super(Machine, self).save(*args, **kwargs)
    
    @ExportMethod(DjangoStruct('Machine'), [DjangoStruct('Machine')], PCGlobal('MANAGE'), [InvalidLogin, CannotSetField])
    @staticmethod
    def create(fields):
        machine = Machine()
        machine.forbid_fields(fields, ['id'])
        machine.update_fields(fields, ['name', 'login', 'address', 'netmask'])
        machine.name = machine.name.strip()
        machine.sort_field = machine.name
        machine.save()
        return machine

    @ExportMethod(DjangoStruct('Machine'), [DjangoId('Machine'), DjangoStruct('Machine')], PCArg('self', 'MANAGE'), [CannotSetField, InvalidLogin])
    def modify(self, fields):
        self.forbid_fields(fields, ['id'])
        self.update_fields(fields, ['name', 'login', 'address', 'netmask'])
        self.name = self.name.strip()
        self.sort_field = self.name
        self.save()
        return self

    @ExportMethod(unicode, [unicode, unicode], PCPermit())
    @staticmethod
    def authenticate(login, password):
        try:
            machine = Machine.objects.get(login=login)
        except Machine.DoesNotExist:
            raise LoginFailed()
        if not machine.check_ip(server_info.client_ip):
            raise LoginFailed()
        if not password_check(machine.password, password):
            raise LoginFailed()
        session = Session.start()
        session.login(machine, 'machine')
        pwhash = password_rehash_old(machine.password, password)
        if pwhash != machine.password:
            machine.password = pwhash
            machine.save()
        return str(token_container.token)

    @ExportMethod(NoneType, [DjangoId('Machine'), unicode], PCArg('self', 'MANAGE'))
    def set_password(self, new_password):
        password_ok(new_password)
        self.password = password_crypt(new_password)
        self.save()

    @ExportMethod(NoneType, [DjangoId('Machine'), unicode], PCArg('self', 'MANAGE'))
    def check_ip(self, ip):
        net = ipaddr.IPv4Network(self.address + '/' + self.netmask)
        addr = ipaddr.IPv4Address(ip)
        return addr in net

class MachineEvents(Events):
    model = Machine
    on_insert = on_update = on_delete = []
