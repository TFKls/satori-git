# vim:ts=4:sts=4:sw=4:expandtab
import select
import psycopg2.extensions
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import connection
from django.db import models
from satori.dbev.events import registry
from satori.events import Event, KeepAlive, Send, Slave

def notifier(connection):
    slave = Slave(connection)
    slave.schedule(notifier_coroutine())
    slave.run()

def row_to_dict(cursor, row):
    res = {}
    for i in range(len(row)):
    	res[cursor.description[i][0]] = row[i]
    return res

def notifier_coroutine():
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
        if select.select([con], [], [], 5) == ([], [], []):
            yield KeepAlive()
        else:
        	con.poll()
        	if con.notifies:
                while con.notifies:
            		con.notifies.pop()
                for notification in notifications.objects.all():

                    modeln = notification.table.split('.')
                    model = models.get_model(modeln[0], modeln[1])
                    obj = model.objects.get(id=notification.object)
                    try:
                        modeln = obj.model.split('.')
                        model = models.get_model(modeln[0], modeln[1])
                        obj = model.objects.get(id=notification.object)
                    except:
                        pass
                    tab = model._meta.db_table + '__version_view'

                    cursor.execute('SELECT * FROM ' + tab + '(' + str(notification.object) + ',' + str(notification.transaction) + ')')
                    rec = row_to_dict(cursor, cursor.fetchone())

                    events = registry._registry[model]
                    if notification.action == 'D' and not notification.entry:
                        version = versions.objects.filter(_version_transaction=notification.transaction).extra(where=[qn(model._meta.pk.column) + ' = ' + str(notification.object)]).get()
                        version.delete()
                        notification.delete()
                        continue
                    event = Event(type='db')
                    event.action = notification.action
                    event.model = rec.model
                    event.object = notification.object
                    event.transaction = notification.transaction
                    event.entry = notification.entry
                    event.user = notification.user
                    if notification.action == 'I' and events.on_insert:
                        for field in events.on_insert:
                            event['new.'+field] = rec[field]
                    if notification.action == 'U' and events.on_update:
                        for field in events.on_update:
                            event['new.'+field] = rec[field]
                    if notification.action == 'D' and events.on_delete:
                        for field in events.on_delete:
                            event['old.'+field] = rec[field]
                    yield Send(event)
                    notification.delete()
