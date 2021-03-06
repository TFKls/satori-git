# vim:ts=4:sts=4:sw=4:expandtab
import base64
import logging
import pickle
import psycopg2.extensions
import select
import time

from django import db
from django.db import connection
from django.db import models
from satori.core.dbev.events import registry
from satori.events import Event
from satori.core.models import Entity

def row_to_dict(cursor, row):
    res = {}
    if row != None:
        for i in range(len(row)):
            res[cursor.description[i][0]] = row[i]
    return res

def handle_notifications(cursor, slave):
    while True:
        transaction = None
        cursor.execute('SELECT min(transaction) AS transaction FROM core_notification')
        res = row_to_dict(cursor, cursor.fetchone())
        if 'transaction' in res and res['transaction'] is not None:
            transaction = int(res['transaction'])
        cursor.execute('SELECT min(transaction) AS transaction FROM core_rawevent')
        res = row_to_dict(cursor, cursor.fetchone())
        if 'transaction' in res and res['transaction'] is not None:
            t = int(res['transaction'])
            if transaction is None or transaction > t:
                transaction = t
        if transaction is None:
            break
        cursor.execute('SELECT * FROM core_notification WHERE transaction=%s', [transaction])
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

            cursor.execute('SELECT model FROM ' + Entity._meta.db_table + '__version_view(%s,%s)', [id, ftrans])
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
                        slave.send(event)
                    if action == 'U' and reg.on_update != None:
                        for field in reg.on_update:
                            if field in rec:
                                event['new.'+field] = rec[field]
                        slave.send(event)
                    if action == 'D' and reg.on_delete != None:
                        for field in reg.on_delete:
                            if field in rec:
                                event['old.'+field] = rec[field]
                        slave.send(event)
                if len(model._meta.parents.items()) > 0:
                    model = model._meta.parents.items()[0][0]
                else:
                    break
        cursor.execute('DELETE FROM core_notification WHERE transaction=%s', [transaction])
        cursor.execute('SELECT * FROM core_rawevent WHERE transaction=%s', [transaction])
        for row in cursor:
            res = row_to_dict(cursor, row)
            event = pickle.loads(base64.urlsafe_b64decode(str(res['data'])))
            slave.send(event)
        cursor.execute('DELETE FROM core_rawevent WHERE transaction=%s', [transaction])

class BackoffDelay(object):
    def __init__(self, min_delay, max_delay):
        self.min_delay = float(min_delay)
        self.max_delay = float(max_delay)
        self.backoff_multiplier = float(1.5)
        self.calm_multiplier = float(5)
        self.last_delay = self.min_delay
        self.last_call = time.time()
    def __call__(self):
        now = time.time()
        delay = self.last_delay
        passed = max(0, now - self.last_call)
        if passed < self.calm_multiplier*self.last_delay:
            delay *= self.backoff_multiplier
        else:
            delay = self.min_delay
        self.last_call = now
        self.last_delay = min(self.max_delay,max(self.min_delay, delay))
        time.sleep(int(self.last_delay))

def run_notifier(slave):
    delay = BackoffDelay(1, 60)
    while True:
        try:
            cursor = connection.cursor()
            con = connection.connection
            con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            con.commit()
            cursor = con.cursor()
            cursor.execute('LISTEN satori;')
            cursor.execute('DELETE FROM core_notification;')

            while True:
                if select.select([con], [], [], 5) == ([], [], []):
                    slave.keep_alive()
                else:
                    con.poll()
                    if con.notifies:
                        while con.notifies:
                            con.notifies.pop()
                        handle_notifications(cursor, slave)
        except GeneratorExit:
            return
        except SystemExit:
            break
        except:
            logging.exception('DBEV notifier error')
            db.close_connection()
            delay()
    slave.disconnect()

