# vim:ts=4:sts=4:sw=4:expandtab
import select
import psycopg2.extensions
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import connection
from django.db import models
from satori.dbev.events import registry
from satori.events.api import Event
from satori.events.protocol import KeepAlive, Send

def notifier():
    qn = connection.ops.quote_name
    qv = lambda x : '\''+str(x)+'\''
    notifications = models.get_model('dbev','notification')
    cursor = connection.cursor()
    con = connection.connection
    con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    con.commit()
    cursor = con.cursor()
    cursor.execute('LISTEN '+notifications.notification+';')

    while True:
        if select.select([cursor], [], [], 5) == ([], [], []):
            yield KeepAlive()
        else:
            while cursor.isready():
                for notification in notifications.objects.all():
                    model = notification.model.split('.')
                    versions = models.get_model(model[0], model[1] + "Versions")
                    model = models.get_model(model[0], model[1])
                    events = registry._registry[model]
                    if notification.action == 'D' and not notification.entry:
                        version = versions.objects.filter(_version_transaction=notification.transaction).extra(where=[qn(model._meta.pk.column) + ' = ' + str(notification.object)]).get()
                        version.delete()
                        notification.delete()
                        continue
                    event = Event(type='db')
                    event.action = notification.action
                    event.model = notification.model
                    event.object = notification.object
                    event.transaction = notification.transaction
                    event.entry = notification.entry
                    event.user = notification.user
                    if notification.action == 'I' and events.on_insert:
                        version = versions.objects.filter(_version_transaction=notification.transaction).extra(where=[qn(model._meta.pk.column) + ' = ' + str(notification.object)]).get()
                        for field in events.on_insert:
                            event['new.'+field] = version.__dict__[field]
                    if notification.action == 'U' and events.on_update:
                        version = versions.objects.filter(_version_transaction=notification.transaction).extra(where=[qn(model._meta.pk.column) + ' = ' + str(notification.object)]).get()
                        previous = versions.objects.filter(_version_transaction=notification.entry).extra(where=[qn(model._meta.pk.column) + ' = ' + str(notification.object)]).get()
                        for field in events.on_update:
                            event['new.'+field] = version.__dict__[field]
                            event['old.'+field] = previous.__dict__[field]
                    if notification.action == 'D' and events.on_delete:
                        previous = versions.objects.filter(_version_transaction=notification.entry).extra(where=[qn(model._meta.pk.column) + ' = ' + str(notification.object)]).get()
                        for field in events.on_delete:
                            event['old.'+field] = previous.__dict__[field]
                    yield Send(event)
                    notification.delete()