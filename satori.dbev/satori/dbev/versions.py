# vim:ts=4:sts=4:sw=4:expandtab
import copy
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import models
import satori.dbev.models
from django.db import connection

class UserField(models.IntegerField):
    def __init__(self, on_init = False, on_update = False, on_delete = False, versions = True):
        super(UserField, self).__init__(self, blank = True, null = True)
        self.on_init = bool(on_init is not False)
        self.on_update = bool(on_update is not False)
        self.on_delete = bool(on_delete is not False)
        self.versions = bool(versions is not False)

    def insert_sql(self, table, fields):
        keys = []
        vals = []
        for key, val in fields.iteritems():
            keys.append(str(key))
            vals.append(str(val))
        return 'INSERT INTO {0} ({1}) VALUES ({2})'.format(table, ', '.join(keys), ', '.join(vals))

    def update_sql(self, table, fields, where):
        return 'UPDATE {0} SET {1} WHERE {2}'.format(table,
            ', '.join([str(key) + " = " + str(val) for key, val in fields.iteritems()]),
            ' AND '.join([str(key) + " = " + str(val) for key, val in where.iteritems()]))

    def delete_sql(self, table, where)
        return 'DELETE FROM {0} WHERE {1}'.format(table,
            ' AND '.join([str(key) + " = " + str(val) for key, val in where.iteritems()]))


    def notify_sql(self, action):
        qn = connection.ops.quote_name
        qv = lambda x : '\''+str(x)+'\''
        if (action == 'I' and self.on_init) or (action == 'U' and self.on_update) or (action == 'D' and self.on_delete):
            entry = qn('old') + "." + qn('_version_transaction')
            if action == 'I':
                entry = 'NULL'
            record = 'new'
            if action == 'D':
                record = 'old'
            notification = models.get_model('dbev','notification')
            not_col = lambda x : qn(notification._meta.get_field_by_name(x)[0].column)
            row = {}
            row[not_col('action')] = qv(action)
            row[not_col('table')]  = qv(self._model._original._meta.app_label + '.' + self._model._original._meta.module_name)
            row[not_col('object')] = qn(record)+'.'+qn(self._model._original._meta.pk.column)
            row[not_col('transaction')] = 'get_transaction_id()'
            row[not_col('previous')] = entry
            row[not_col('user')] = 'get_user_id()'
            where = {}
            where[not_col('table')] = row[not_col('table')]
            where[not_col('object')] = row[not_col('object')]
            where[not_col('transaction')] = row[not_col('transaction')]
            upd = row.copy()
            if action == 'U':
                del upd[not_col('action')]
            del upd[not_col('previous')]
            if action == 'I':
                return """
                    {0};
                    NOTIFY {1};
                """.format(
                    self.insert_sql(qn(notification._meta.db_table), row),
                    qn(notification.notification)
                )
            return """
                {0};
                IF NOT found THEN
                    {1};
                END IF;
                NOTIFY {2};
            """.format(
                self.update_sql(qn(notification._meta.db_table), upd, where),
                self.insert_sql(qn(notification._meta.db_table), row),
                qn(notification.notification)
            )
        return ''

    def post_create_sql(self, style, db_table):
        qn = connection.ops.quote_name
        qv = lambda x : '\''+str(x)+'\''

        tabs = []
        keys = []
        mod = self._model._original
        while issubclass(mod, models.Model):
        	tabs.append(str(mod._meta.db_table))
        	keys.append(str(mod._meta.pk.column))
            try:
            	mod = mod._meta.parents.items()[0][0]
            except:
                break

        modify_original = """
            ALTER TABLE {0} ADD COLUMN {1} integer NOT NULL DEFAULT get_transaction_id();
            SELECT create_version_table({2}, {3});
            SELECT create_full_view({4}, {5});
            SELECT create_version_function({4}, {5});
        """.format(
            qn(self._model._original._meta.db_table),
            qn('_version_transaction'),
            qv(self._model._original._meta.db_table),
            qv(self._model._original._meta.pk.column),
            'ARRAY[' + ','.join([qv(tab) for tab in tabs]) + ']',
            'ARRAY[' + ','.join([qv(key) for key in keys]) + ']',
        )
       
        row = {}
        for x in self._model._original._meta.local_fields:
            row[qn(x.column)] = qn('new')+'.'+qn(x.column)
        row[qn('_version_transaction')] = 'get_transaction_id()'
        row[qn('_version_prev')] = 'get_transaction_id()'
        row[qn('_version_user')] = 'get_user_id()'


        insert_trigger = """
            CREATE OR REPLACE FUNCTION {0}() RETURNS TRIGGER AS $$
            BEGIN
                {1};
                {2}
                RETURN {3};
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER {4} AFTER INSERT ON {5} FOR EACH ROW EXECUTE PROCEDURE {0}();
        """.format(
            qn('on_after_insert_' + self._model._original._meta.db_table),
            self.insert_sql(qn(db_table), row),
            self.notify_sql('I'),
            qn('new'),
            qn('after_insert_' + self._model._original._meta.db_table),
            qn(self._model._original._meta.db_table),
        )

        row[qn('_version_prev')] = qn('old')+'.'+qn('_version_transaction')
        where = {}
        where[qn(self._model._original._meta.pk.column)] = row[qn(self._model._original._meta.pk.column)]
        where[qn('_version_transaction')] = row[qn('_version_transaction')]
        upd = row.copy()
        del upd[qn('_version_prev')]

        update_trigger = """
            CREATE OR REPLACE FUNCTION {0}() RETURNS TRIGGER AS $$
            BEGIN
                IF old <> new THEN
                    new._version_transaction = get_transaction_id();
                END IF;
                RETURN new;
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER {2} BEFORE UPDATE ON {3} FOR EACH ROW EXECUTE PROCEDURE {0}();

            CREATE OR REPLACE FUNCTION {4}() RETURNS TRIGGER AS $$
            BEGIN
                IF old = new THEN
                    RETURN new;
                END IF;
                UPDATE {5} SET _version_next = get_transaction_id() WHERE {6} = {7} AND _version_next IS NULL;
                {8};
                IF NOT found THEN
                    {9};
                END IF;
                {10}
                RETURN new;
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER {11} AFTER UPDATE ON {3} FOR EACH ROW EXECUTE PROCEDURE {4}();
        """.format(
            qn('on_before_update_' + self._model._original._meta.db_table),
            qn('new'),
            qn('before_update_' + self._model._original._meta.db_table),
            qn(self._model._original._meta.db_table),
            qn('on_after_update_' + self._model._original._meta.db_table),
            qn(db_table),
            qn(self._model._original._meta.pk.column),
            qn('new')+'.'+qn(self._model._original._meta.pk.column),
            self.update_sql(qn(db_table), upd, where),
            self.insert_sql(qn(db_table), row),
            self.notify_sql('U'),
            qn('after_update_' + self._model._original._meta.db_table),
        )

        for x in self._model._original._meta.local_fields:
            row[qn(x.column)] = qn('old')+'.'+qn(x.column)
            upd[qn(x.column)] = qn('old')+'.'+qn(x.column)
        where[qn(self._model._original._meta.pk.column)] = row[qn(self._model._original._meta.pk.column)]
        row[qn('_version_to')] = 'CURRENT_TIMESTAMP'
        upd[qn('_version_to')] = 'CURRENT_TIMESTAMP'

        delete_trigger = """
            CREATE OR REPLACE FUNCTION {0}() RETURNS TRIGGER AS $$
            BEGIN
                UPDATE {1} SET _version_next = get_transaction_id() WHERE {2} = {3} AND _version_next IS NULL;
                DELETE FROM {1} WHERE {2} = {3} AND _version_transaction = get_transaction_id();
                {6}
                RETURN {7};
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER {8} AFTER DELETE ON {9} FOR EACH ROW EXECUTE PROCEDURE {0}();
        """.format(
            qn('on_after_delete_' + self._model._original._meta.db_table),
            qn(db_table),
            qn(self._model._original._meta.pk.column),
            qn('old')+'.'+qn(self._model._original._meta.pk.column),
            self.update_sql(qn(db_table), upd, where),
            self.insert_sql(qn(db_table), row),
            self.notify_sql('D'),
            qn('old'),
            qn('after_delete_' + self._model._original._meta.db_table),
            qn(self._model._original._meta.db_table),
        )



        return (modify_original, insert_trigger, update_trigger, delete_trigger)

class Versions:
    def __init__(self, model, events):
        class PMeta(models.base.ModelBase):
            def __new__(cls, name, bases, attrs):
                return type.__new__(cls, name, bases, attrs)
        
        fields = {}
        fields['__module__'] = model.__module__

        for field in model._meta.local_fields:
        	if isinstance(field, models.fields.AutoField) or \
        		isinstance(field, models.fields.related.OneToOneField) or \
        		isinstance(field, models.fields.related.ForeignKey):
                nfield = models.fields.IntegerField(
                    name=field.name,
                    verbose_name=field.verbose_name,
                    db_column=field.column,
                    null=True,
                )
            else:
            	nfield = copy.copy(field)
            #TODO: nfield.unique = False
            nfield._original = field
            fields[field.name] = nfield

        fields['_version_id'] = models.AutoField(primary_key=True)
        fields['_version_transaction'] = models.IntegerField()
        fields['_version_prev'] = models.IntegerField(null=True, blank=True)
        fields['_version_next'] = models.IntegerField(null=True, blank=True)
        fields['_version_user'] = UserField(events.on_insert, events.on_update, events.on_delete, events.versions)
        class Meta(object):
            db_table = model._meta.db_table + '__versions'
        fields['Meta'] = Meta
        modelclass = models.base.ModelBase.__new__(PMeta, model.__name__+"Versions", (models.Model,), fields)
        modelclass._original = model
        for field in modelclass._meta.fields:
            field._model = modelclass

def setUserId(uid):
    connection.cursor().execute('SELECT set_user_id(%s);', [str(int(uid))])

def unsetUserId():
    connection.cursor().execute('SELECT set_user_id(NULL);')
