# vim:ts=4:sts=4:sw=4:expandtab
import select
import psycopg2.extensions
import traceback
from django.db import connection
from django.db import models
from satori.dbev.events import registry
from satori.events import Event, KeepAlive, Send, Slave
from satori.core.models import Object

def notifier(connection):
    slave = Slave(connection)
    slave.schedule(notifier_coroutine())
    slave.run()

def row_to_dict(cursor, row):
    res = {}
    if row != None:
        for i in range(len(row)):
            res[cursor.description[i][0]] = row[i]
    return res

def handle_notifications(cursor):
    while True:
        cursor.execute('SELECT min(transaction) AS transaction FROM dbev_notification')
        res = row_to_dict(cursor, cursor.fetchone())
        if 'transaction' not in res:
            break
        if res['transaction'] == None:
            break
        transaction = int(res['transaction'])
        cursor.execute('SELECT * FROM dbev_notification WHERE transaction=%s', [transaction])
        events = {}
        for row in cursor:
            res = row_to_dict(cursor, row)
            if 'object' not in res:
                continue
            id = int(res['object'])
            table = str(res['table'])
            if id not in events:
                events[id] = {}
            events[id][table] = res
        for id, tables in events.iteritems():
            action = ''
            user = None
            previous = None
            for table, data in tables.iteritems():
                action = data['action']
                if data['user'] != None:
                    user = int(data['user'])
                if data['previous'] != None:
                    if previous == None or previous < int(data['previous']):
                        previous = int(data['previous'])

            if action == 'D':
                ftrans = transaction-1
            else:
                ftrans = transaction

            cursor.execute('SELECT model FROM ' + Object._meta.db_table + '__version_view(%s,%s)', [id, ftrans])
            res = row_to_dict(cursor, cursor.fetchone())
            if 'model' not in res:
                continue
            modelname = res['model']
            model = models.get_model(*modelname.split('.'))
            basemodel = model;
            for table, data in tables.iteritems():
                newmodel = models.get_model(*table.split('_', 1))
                if issubclass(basemodel, newmodel):
                    basemodel = newmodel

            cursor.execute('SELECT * FROM ' + model._meta.db_table + '__version_view(%s,%s)', [id, ftrans])
            rec = row_to_dict(cursor, cursor.fetchone())
            while issubclass(model, basemodel):
                event = Event(type='db')
                event.object_id = id
                event.transaction = transaction
                event.action = action
                event.user = user
                event.previous = previous
                event.model = model._meta.app_label + '.' + model._meta.module_name
                if model in registry:
                    reg = registry[model]
                    if action == 'I' and reg.on_insert != None:
                        for field in reg.on_insert:
                            if field in rec:
                                event['new.'+field] = rec[field]
                        yield Send(event)
                    if action == 'U' and reg.on_update != None:
                        for field in reg.on_update:
                            if field in rec:
                                event['new.'+field] = rec[field]
                        yield Send(event)
                    if action == 'D' and reg.on_delete != None:
                        for field in reg.on_delete:
                            if field in rec:
                                event['old.'+field] = rec[field]
                        yield Send(event)
                if len(model._meta.parents.items()) > 0:
                    model = model._meta.parents.items()[0][0]
                else:
                    break
        cursor.execute('DELETE FROM dbev_notification WHERE transaction=%s', [int(transaction)])


def notifier_coroutine():
    while True:
        try:
            cursor = connection.cursor()
            con = connection.connection
            con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            con.commit()
            cursor = con.cursor()
            cursor.execute('LISTEN satori;')
            for action in handle_notifications(cursor):
            	yield action

            while True:
                if select.select([con], [], [], 5) == ([], [], []):
                    yield KeepAlive()
                else:
                    con.poll()
                    if con.notifies:
                        while con.notifies:
                            con.notifies.pop()
                        for action in handle_notifications(cursor):
                            yield action
        except GeneratorExit:
            break
        except:
            traceback.print_exc()
