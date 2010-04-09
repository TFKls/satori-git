# vim:ts=4:sts=4:sw=4:expandtab
import select
import psycopg2.extensions
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import connection
from django.db import models
import satori.dbev.models
from satori.dbev.events import registry
from satori.core.events.api import Event, QueueId
from satori.core.events.protocol import KeepAlive, Attach, Detach, Map, Unmap, Send, Receive

def notifier():
    qn = connection.ops.quote_name
    qv = lambda x : '\''+str(x)+'\''
    notification = models.get_model('dbev','notification')
    cursor = connection.cursor()
    con = connection.connection
    con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    con.commit()
    cursor = con.cursor()
    cursor.execute('LISTEN '+notification.notification+';')

    while True:
        if select.select([cursor],[],[],5)==([],[],[]):
            yield KeepAlive()
        else:
            while cursor.isready():
                for n in notification.objects.all():
                    model = n.model.split('.')
                    versions = models.get_model(model[0], model[1] + "Versions")
                    model = models.get_model(model[0], model[1])
                    events = registry._registry[model]
                    if n.action == 'D' and not n.entry:
                        v = versions.objects.filter(_version_transaction=n.transaction).extra(where=[qn(model._meta.pk.column) + ' = ' + str(n.object)]).get()
                        v.delete()
                        n.delete()
                        continue
                    event = Event(type='db')
                    event.action = n.action
                    event.model = n.model
                    event.object = n.object
                    event.transaction = n.transaction
                    event.entry = n.entry
                    event.user = n.user
                    if n.action == 'I' and events.on_insert:
                        v = versions.objects.filter(_version_transaction=n.transaction).extra(where=[qn(model._meta.pk.column) + ' = ' + str(n.object)]).get()
                        for f in events.on_insert:
                            print f
                            event['new.'+f] = v.__dict__[f]
                    if n.action == 'U' and events.on_update:
                        v = versions.objects.filter(_version_transaction=n.transaction).extra(where=[qn(model._meta.pk.column) + ' = ' + str(n.object)]).get()
                        p = versions.objects.filter(_version_transaction=n.entry).extra(where=[qn(model._meta.pk.column) + ' = ' + str(n.object)]).get()
                        for f in events.on_update:
                            print f
                            event['new.'+f] = v.__dict__[f]
                            event['old.'+f] = p.__dict__[f]
                    if n.action == 'D' and events.on_delete:
                        p = versions.objects.filter(_version_transaction=n.entry).extra(where=[qn(model._meta.pk.column) + ' = ' + str(n.object)]).get()
                        for f in events.on_delete:
                            print f
                            event['old.'+f] = p.__dict__[f]
                    yield Send(event)
                    n.delete()
