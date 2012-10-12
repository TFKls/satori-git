# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Printer(Entity):
    """Model. A Printer.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_printer')

    name          = models.CharField(max_length=64, unique=True)
    description   = models.TextField(blank=True, default="")
    script        = models.TextField(blank=False, default="")

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('description', 'VIEW'), ('script', 'MANAGE')]
    
    def save(self, *args, **kwargs):
        super(Printer, self).save(*args, **kwargs)

    def __str__(self):
        return self.name+" ("+self.description+")"

    @ExportMethod(DjangoStruct('Printer'), [DjangoStruct('Printer')], PCGlobal('ADMIN'), [CannotSetField])
    @staticmethod
    def create(fields):
        printer = Printer()
        printer.forbid_fields(fields, ['id'])
        modified = printer.update_fields(fields, ['name', 'description', 'script'])
        printer.save()
        Privilege.grant(Global.get_instance().authenticated, printer, 'VIEW')
        return printer
        
    @ExportMethod(DjangoStruct('Printer'), [DjangoId('Printer'), DjangoStruct('Printer')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id'])
        modified = self.update_fields(fields, ['name', 'description', 'script'])
        self.save()
        return self

    @ExportMethod(NoneType, [DjangoId('Printer')], PCArg('self', 'MANAGE'))
    def delete(self):
        try:
            super(Printer, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

class PrinterEvents(Events):
    model = Printer
    on_insert = on_update = on_delete = []
