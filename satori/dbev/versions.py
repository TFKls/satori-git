# vim:ts=4:sts=4:sw=4:expandtab
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import models
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

    def notify_sql(self, action):
        qn = connection.ops.quote_name
        qv = lambda x : '\''+str(x)+'\''
        if (action == 'I' and self.on_init) or (action == 'U' and self.on_update) or (action == 'D' and self.on_delete):
            record = 'new'
            if action == 'D':
                record = 'old'
            notification = models.get_model('dbev','notification')
            return """
                INSERT INTO {0} ({1}) VALUES ({2});
                NOTIFY {3};
            """.format(
                qn(notification._meta.db_table),
                ','.join([qn(notification._meta.get_field_by_name(x)[0].column) for x in [
                    'action',
                    'model',
                    'object',
                    'version',
                    'transaction',
                    'user']]),
                ','.join([
                    qv(action),
                    qv(self._model._original._meta.app_label + '.' + self._model._original._meta.module_name),
                    qn(record)+'.'+qn(self._model._original._meta.pk.column),
                    'currval(\'' + self._model._meta.db_table + '_' + self._model._meta.pk.column + '_seq' + '\')',
                    'get_transaction_id()',
                    'get_user_id()']),
                qn(notification.notification)
            )
        return ''

    def post_create_sql(self, style, db_table):
        qn = connection.ops.quote_name
        qv = lambda x : '\''+str(x)+'\''
        notification = models.get_model('dbev', 'notification')

        nextval = 'nextval(\'' + self._model._meta.db_table + '_' + self._model._meta.pk.column + '_seq' + '\')'
        
        insert_trigger = """
            CREATE OR REPLACE FUNCTION {0}() RETURNS TRIGGER AS $$
            BEGIN
                UPDATE {1} SET _version_to = CURRENT_TIMESTAMP WHERE {2} = {3} AND _version_to IS NULL;
                INSERT INTO {1} ({4}) VALUES ({5});
                {6}
                RETURN {7};
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER {8} AFTER INSERT ON {9} FOR EACH ROW EXECUTE PROCEDURE {0}();
        """.format(
            qn('on_after_insert_' + self._model._original._meta.db_table),
            qn(db_table),
            qn(self._model._original._meta.pk.column),
            qn('new')+'.'+qn(self._model._original._meta.pk.column),
            ','.join([qn(x.column) for x in self._model._original._meta.local_fields] + [qn(x) for x in ['_version_id', '_version_from', '_version_to', '_version_transaction', '_version_user']]),
            ','.join([qn('new')+'.'+qn(x.column) for x in self._model._original._meta.local_fields] + [nextval, 'CURRENT_TIMESTAMP', 'NULL', 'get_transaction_id()', 'get_user_id()']),
            self.notify_sql('I'),
            qn('new'),
            qn('after_insert_' + self._model._original._meta.db_table),
            qn(self._model._original._meta.db_table),
        )

        update_trigger = """
            CREATE OR REPLACE FUNCTION {0}() RETURNS TRIGGER AS $$
            BEGIN
                UPDATE {1} SET _version_to = CURRENT_TIMESTAMP WHERE {2} = {3} AND _version_to IS NULL;
                INSERT INTO {1} ({4}) VALUES ({5});
                {6}
                RETURN {7};
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER {8} AFTER UPDATE ON {9} FOR EACH ROW EXECUTE PROCEDURE {0}();
        """.format(
            qn('on_after_update_' + self._model._original._meta.db_table),
            qn(db_table),
            qn(self._model._original._meta.pk.column),
            qn('new')+'.'+qn(self._model._original._meta.pk.column),
            ','.join([qn(x.column) for x in self._model._original._meta.local_fields] + [qn(x) for x in ['_version_id', '_version_from', '_version_to', '_version_transaction', '_version_user']]),
            ','.join([qn('new')+'.'+qn(x.column) for x in self._model._original._meta.local_fields] + [nextval, 'CURRENT_TIMESTAMP', 'NULL', 'get_transaction_id()', 'get_user_id()']),
            self.notify_sql('U'),
            qn('new'),
            qn('after_update_' + self._model._original._meta.db_table),
            qn(self._model._original._meta.db_table),
        )

        delete_trigger = """
            CREATE OR REPLACE FUNCTION {0}() RETURNS TRIGGER AS $$
            BEGIN
                UPDATE {1} SET _version_to = CURRENT_TIMESTAMP WHERE {2} = {3} AND _version_to IS NULL;
                INSERT INTO {1} ({4}) VALUES ({5});
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
            ','.join([qn(x.column) for x in self._model._original._meta.local_fields] + [qn(x) for x in ['_version_id', '_version_from', '_version_to', '_version_transaction', '_version_user']]),
            ','.join([qn('old')+'.'+qn(x.column) for x in self._model._original._meta.local_fields] + [nextval, 'CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP', 'get_transaction_id()', 'get_user_id()']),
            self.notify_sql('D'),
            qn('old'),
            qn('after_delete_' + self._model._original._meta.db_table),
            qn(self._model._original._meta.db_table),
        )

        return (insert_trigger, update_trigger, delete_trigger);

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
        fields['_version_id'] = models.AutoField(primary_key=True)
        fields['_version_from'] = models.DateTimeField()
        fields['_version_to'] = models.DateTimeField(null=True, blank=True)
        fields['_version_transaction'] = models.IntegerField()
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
