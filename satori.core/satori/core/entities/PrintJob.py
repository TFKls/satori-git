# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity, Contest

@ExportModel
class PrintJob(Entity):
    """Model. Single print job.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_printjob')

    contestant    = models.ForeignKey('Contestant', related_name='printjobs', on_delete=models.CASCADE)
    contest       = models.ForeignKey('Contest', related_name='printjobs', on_delete=models.CASCADE)
    time          = models.DateTimeField(auto_now_add=True)

    data          = AttributeGroupField(PCArg('self', 'VIEW'), PCDeny(), '')

    class ExportMeta(object):
        fields = [('contestant', 'VIEW'), ('contest', 'VIEW'), ('time', 'VIEW')]

    class RightsMeta(object):
        inherit_parent = 'contestant'
        inherit_parent_MANAGE = ['MANAGE']
        inherit_parent_VIEW = ['VIEW_SUBMIT_CONTENTS']

    def save(self, *args, **kwargs):
        self.fixup_data()
        super(PrintJob, self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('PrintJob'), [DjangoStruct('PrintJob'), Binary, unicode], PCArgField('fields', 'contest', 'PERMIT_PRINT'), [CannotSetField])
    @staticmethod
    def create(fields, content, filename):
        printjob = PrintJob()
        printjob.contestant = fields.contest.find_contestant(token_container.token.role)
        printjob.forbid_fields(fields, ['id', 'contestant', 'time'])
        printjob.update_fields(fields, ['contest'])
        printjob.save()
        blob = printjob.data_set_blob('content', filename=filename)
        blob.write(content)
        blob.close()
        RawEvent().send(Event(type='printjob', id=printjob.id))
        return printjob

    @ExportMethod(NoneType, [DjangoId('PrintJob')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            super(PrintJob, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

    @ExportMethod(NoneType, [DjangoId('PrintJob')], PCArg('self', 'MANAGE'))
    def reprint(self):
        RawEvent().send(Event(type='printjob', id=self.id))

class PrintJobEvents(Events):
    model = PrintJob
    on_insert = on_update = on_delete = []
