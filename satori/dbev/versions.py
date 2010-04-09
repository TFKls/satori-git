# vim:ts=4:sts=4:sw=4:expandtab
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import models
import satori.dbev.models
from django.db import connection

class VersionsField(models.Field):
    def __init__(self, _original):
        self._original = _original
        super(VersionsField, self).__init__(self, blank = True, null = True, db_column = _original.column, primary_key = False)

    def db_type(self, connection):
        if self._original.db_type() == "serial":
            return "integer"
        else:
            return self._original.db_type()

class UserField(models.IntegerField):
    def __init__(self, on_init = False, on_update = False, on_delete = False, versions = True):
        super(UserField, self).__init__(self, blank = True, null = True)
        self.on_init = bool(on_init is not False)
        self.on_update = bool(on_update is not False)
        self.on_delete = bool(on_delete is not False)
        self.versions = bool(versions is not False)

    def insert_sql(self, table, dict):
        keys = []
        vals = []
        for k,v in dict.iteritems():
        	keys.append(str(k))
        	vals.append(str(v))
        return 'INSERT INTO {0} ({1}) VALUES ({2})'.format(table, ', '.join(keys), ', '.join(vals))

    def update_sql(self, table, dict, where = {}):
        if where:
            return 'UPDATE {0} SET {1} WHERE {2}'.format(table,
                ', '.join([str(x) + " = " + str(y) for x,y in dict.iteritems()]),
                ' AND '.join([str(x) + " = " + str(y) for x,y in where.iteritems()]))
        else:
            return 'UPDATE {0} SET {1}'.format(table, ', '.join([str(x) + " = " + str(y) for x,y in dict.iteritems()]))

    def notify_sql(self, action):
        qn = connection.ops.quote_name
        qv = lambda x : '\''+str(x)+'\''
        if (action == 'I' and self.on_init) or (action == 'U' and self.on_update) or (action == 'D' and self.on_delete):
            entry = qn('old') + "." + qn('_version_transaction');
            if action == 'I':
                entry = 'NULL'
            record = 'new'
            if action == 'D':
                record = 'old'
            notification = models.get_model('dbev','notification')
            not_col = lambda x : qn(notification._meta.get_field_by_name(x)[0].column)
            row = {}
            row[not_col('action')] = qv(action)
            row[not_col('model')]  = qv(self._model._original._meta.app_label + '.' + self._model._original._meta.module_name)
            row[not_col('object')] = qn(record)+'.'+qn(self._model._original._meta.pk.column)
            row[not_col('transaction')] = 'get_transaction_id()'
            row[not_col('entry')] = entry
            row[not_col('user')] = 'get_user_id()'
            where = {}
            where[not_col('model')] = row[not_col('model')]
            where[not_col('object')] = row[not_col('object')]
            where[not_col('transaction')] = row[not_col('transaction')]
            upd = row.copy()
            if action == 'U':
            	del upd[not_col('action')]
            del upd[not_col('entry')]
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
        notification = models.get_model('dbev', 'notification')

        modify_original = """
            ALTER TABLE {0} ADD COLUMN {1} integer NOT NULL DEFAULT get_transaction_id();
            CREATE INDEX {7} ON {2} ({3});
            CREATE INDEX {8} ON {2} ({4});
            CREATE UNIQUE INDEX {9} ON {2} ({5},{6});
        """.format(
            qn(self._model._original._meta.db_table),
            qn('_version_transaction'),
            qn(db_table),
            qn('_version_from'),
            qn('_version_to'),
            qn('_version_transaction'),
            qn(self._model._original._meta.pk.column),
            qn(db_table + '_vfrom_idx'),
            qn(db_table + '_vto_idx'),
            qn(db_table + '_ver_idx'),
        )
       
        row = {}
        for x in self._model._original._meta.local_fields:
        	row[qn(x.column)] = qn('new')+'.'+qn(x.column)
        row[qn('_version_from')] = 'CURRENT_TIMESTAMP'
        row[qn('_version_to')] = 'NULL'
        row[qn('_version_transaction')] = 'get_transaction_id()'
        row[qn('_version_entry')] = 'NULL'
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

        row[qn('_version_entry')] = qn('old')+'.'+qn('_version_transaction');
        where = {}
        where[qn(self._model._original._meta.pk.column)] = row[qn(self._model._original._meta.pk.column)]
        where[qn('_version_transaction')] = row[qn('_version_transaction')]
        upd = row.copy()
        del upd[qn('_version_entry')]

        update_trigger = """
            CREATE OR REPLACE FUNCTION {0}() RETURNS TRIGGER AS $$
            BEGIN
                {1}._version_transaction = get_transaction_id();
                RETURN {1};
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER {2} BEFORE UPDATE ON {3} FOR EACH ROW EXECUTE PROCEDURE {0}();

            CREATE OR REPLACE FUNCTION {4}() RETURNS TRIGGER AS $$
            BEGIN
                UPDATE {5} SET _version_to = CURRENT_TIMESTAMP WHERE {6} = {7} AND _version_to IS NULL;
                {8};
                IF NOT found THEN
                    {9};
                END IF;
                {10}
                RETURN {1};
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
                UPDATE {1} SET _version_to = CURRENT_TIMESTAMP WHERE {2} = {3} AND _version_to IS NULL;
                {4};
                IF NOT found THEN
                    {5};
                END IF;
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
        
        class PModel(models.Model):
            __metaclass__ = PMeta
            pass

        fields = {}
        fields['__module__'] = model.__module__
        for field in model._meta.local_fields:
            fields[field.name] = VersionsField(field)
        fields['_version_from'] = models.DateTimeField()
        fields['_version_to'] = models.DateTimeField(null=True, blank=True)
        fields['_version_transaction'] = models.IntegerField()
        fields['_version_entry'] = models.IntegerField(null=True, blank=True)
        fields['_version_user'] = UserField(events.on_insert, events.on_update, events.on_delete, events.versions)
        class Meta(object):
            db_table = model._meta.db_table + '__versions'
        fields['Meta'] = Meta
        modelclass = models.base.ModelBase.__new__(PMeta, model.__name__+"Versions", (models.Model,), fields)
        modelclass._original = model
        for field in modelclass._meta.fields:
            field._model = modelclass

def set_user_id(id):
    connection.cursor().execute('SELECT set_user_id(%s);', [str(int(id))])

def unset_user_id():
    connection.cursor().execute('SELECT set_user_id(NULL);')
