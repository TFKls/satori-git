# vim:ts=4:sts=4:sw=4:expandtab
from django.db import models
from satori.core.models import Entity
from satori.core.dbev.events import registry


def install_versions_sql(model):
    qv = lambda x : '\''+str(x)+'\''
    tabs = []
    keys = []
    mod = model
    while issubclass(mod, models.Model):
        tabs.append(str(mod._meta.db_table))
        keys.append(str(mod._meta.pk.column))
        if len(mod._meta.parents.items()) > 0:
            mod = mod._meta.parents.items()[0][0]
        else:
            break

    return """
        SELECT install_versions({0}, {1}, {2}, {3}, 'satori');
    """.format(
        qv(model._meta.db_table),
        qv(model._meta.pk.column),
        'ARRAY[' + ','.join([qv(tab) for tab in tabs]) + ']',
        'ARRAY[' + ','.join([qv(key) for key in keys]) + ']',
    )

def install_rights_sql():
    qv = lambda x : '\''+str(x)+'\''
    dirty = {}
    sql = """
CREATE OR REPLACE FUNCTION right_inheritance_update(_id INTEGER) RETURNS VOID AS $$
BEGIN
    PERFORM right_inheritance_clear(_id);
    CASE (SELECT model FROM core_entity WHERE id=_id)"""

    for model in sorted(registry.keys(), key=lambda m: m._meta.db_table):
        if issubclass(model, Entity):
            model_name = model._meta.app_label + '.' + model._meta.module_name
            sql += """
            WHEN {0} THEN """.format(qv(model_name))
            for right, list in model.inherit_rights().items():
                for pent, pright in list:
                    if pent:
                        dirty_model = model._meta.get_field(pent).model
                        dirty_column = model._meta.get_field(pent).column
                        if dirty_model not in dirty:
                        	dirty[dirty_model] = set()
                        dirty[dirty_model].add(dirty_column)
                        sql += """
                PERFORM right_inheritance_add(_id, {0}, (SELECT {1} FROM {2} WHERE id=_id), {3});""".format(
                            qv(right),
                            dirty_column,
                            model._meta.db_table + '__view',
                            qv(pright))
                    else:
                        sql += """
                PERFORM right_inheritance_add(_id, {0}, (SELECT id FROM core_global__view), {1});""".format(
                            qv(right),
                            qv(pright))
    sql += """
    END CASE;
END;
$$ LANGUAGE plpgsql;
"""

    ret = []
    ret.append(sql)

    for model in sorted(registry.keys(), key=lambda m: m._meta.db_table):
        if issubclass(model, Entity):
            model_name = model._meta.app_label + '.' + model._meta.module_name
            trig  = 'CREATE OR REPLACE FUNCTION ' + model._meta.db_table + '__after_insert_update_rights_trigger() RETURNS TRIGGER AS $$ '
            trig += 'BEGIN IF (SELECT model FROM core_entity WHERE id=new.' + model._meta.pk.column + ') = \'' + model_name + '\' THEN '
            trig += 'PERFORM right_inheritance_update(new.' + model._meta.pk.column + ');'
            trig += 'END IF;'
            trig += 'RETURN new; END; $$ LANGUAGE plpgsql;'
            trig += 'CREATE TRIGGER ' + model._meta.db_table + '__after_insert_update_rights AFTER INSERT ON ' + model._meta.db_table + ' FOR EACH ROW EXECUTE PROCEDURE ' + model._meta.db_table + '__after_insert_update_rights_trigger();'
            ret.append(trig)

    for model in dirty:
        trig  = 'CREATE OR REPLACE FUNCTION ' + model._meta.db_table + '__after_update_update_rights_trigger() RETURNS TRIGGER AS $$ '
        trig += 'BEGIN IF '
        trig += ' OR '.join([ 'old.' + x + ' <> ' + 'new.' + x for x in dirty[model]])
        trig += ' THEN PERFORM right_inheritance_update(new.' + model._meta.pk.column + '); END IF;'
        trig += 'RETURN new; END; $$ LANGUAGE plpgsql;'
        trig += 'CREATE TRIGGER ' + model._meta.db_table + '__after_update_update_rights AFTER UPDATE ON ' + model._meta.db_table + ' FOR EACH ROW EXECUTE PROCEDURE ' + model._meta.db_table + '__after_update_update_rights_trigger();'
        ret.append(trig)

    ret.append('SELECT right_inheritance_update(id) FROM core_entity;')
    return ret

def install_dbev_sql():
    set_user_id_function = """
CREATE OR REPLACE FUNCTION set_user_id(arg INTEGER) RETURNS VOID AS $$
BEGIN
    DROP TABLE IF EXISTS user_id;
    CREATE TEMPORARY TABLE user_id (id) AS VALUES (arg);

    DROP TABLE IF EXISTS user_roles;
    CREATE TEMPORARY TABLE user_roles (role_id) 
        AS SELECT keyid AS role_id
            FROM connectby('core_rolemapping'::text, 'parent_id'::text, 'child_id'::text, arg::text, 0)
                AS t(keyid INT, parent_keyid INT, level INT);
END;
$$ LANGUAGE plpgsql;
"""
    get_user_id_function = """
CREATE OR REPLACE FUNCTION get_user_id() RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT id FROM user_id);
EXCEPTION
    WHEN undefined_table THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""
    transaction_id_seq = """
DROP SEQUENCE IF EXISTS transaction_id_seq;
CREATE SEQUENCE transaction_id_seq;
"""
    get_transaction_id_function = """
CREATE OR REPLACE FUNCTION get_transaction_id() RETURNS INTEGER AS $$
DECLARE
    _xid TEXT;
    _id INTEGER;
BEGIN
    _xid := (SELECT virtualxid FROM pg_locks WHERE locktype='virtualxid' and pid=pg_backend_pid());
    _id := (SELECT id FROM transaction_id WHERE xid=_xid);
    IF _id IS NULL THEN
        _id := nextval('transaction_id_seq');
        DELETE FROM transaction_id;
        INSERT INTO transaction_id VALUES(_xid, _id);
        RETURN _id;
    END IF;
    RETURN _id;
EXCEPTION
    WHEN undefined_table THEN
        CREATE TEMPORARY TABLE transaction_id(xid TEXT, id INTEGER);
        _id := nextval('transaction_id_seq');
        INSERT INTO transaction_id VALUES(_xid, _id);
        RETURN _id;
END;
$$ LANGUAGE plpgsql;
"""
    insert_rawevent_trigger = """
CREATE OR REPLACE FUNCTION core_rawevent__before_insert_trigger() RETURNS TRIGGER AS $$
BEGIN
  new.transaction := get_transaction_id();
  NOTIFY satori;
  RETURN new;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER core_rawevent__before_insert BEFORE INSERT ON core_rawevent FOR EACH ROW EXECUTE PROCEDURE core_rawevent__before_insert_trigger();
"""

    create_version_table_function = """
CREATE OR REPLACE FUNCTION create_version_table(_table TEXT, _key TEXT) RETURNS TEXT AS $$
DECLARE
    _exec TEXT := '';
    _texec TEXT := '';
    _vtable TEXT;
    _cols TEXT[];
    _rec RECORD;
    i INTEGER;
    j INTEGER;
BEGIN
    _exec := 'ALTER TABLE ' || quote_ident(_table) || ' ADD COLUMN _version_transaction integer NOT NULL DEFAULT get_transaction_id();';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    _vtable := _table || '__versions';
    _exec := 'DROP TABLE IF EXISTS ' || quote_ident(_vtable);
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    _exec := 'CREATE TABLE ' || quote_ident(_vtable) || ' (';
    FOR _rec in (
        SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS type from pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE c.relname=_table AND a.attnum > 0 ORDER BY a.attnum
    ) LOOP
        IF _rec.attname <> '_version_transaction' THEN
            _exec := _exec || quote_ident(_rec.attname) || ' ' || _rec.type;
            IF _rec.attname = _key THEN
                _exec := _exec || ' NOT NULL';
            END IF;
            _exec := _exec || ',';
        END IF;
    END LOOP;
    _exec := _exec || '_version_transaction integer NOT NULL,';
    _exec := _exec || '_version_prev integer,';
    _exec := _exec || '_version_next integer,';
    _exec := _exec || '_version_user integer,';
    _exec := _exec || '_version_date timestamp with time zone default now(),';
    _exec := _exec || 'PRIMARY KEY(' || quote_ident(_key) || ',_version_transaction)';
    _exec := _exec || ')';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    RETURN _texec;
END;
$$ LANGUAGE plpgsql;
"""

    create_full_view_function = """
CREATE OR REPLACE FUNCTION create_full_view(_tables TEXT[], _keys TEXT[]) RETURNS TEXT AS $$
DECLARE
    _exec TEXT := '';
    _name TEXT;
    _cols TEXT[];
    _vers TEXT[];
    _rec RECORD;
    i INTEGER;
    j INTEGER;
BEGIN
    i := array_lower(_tables, 1);
    _name := quote_ident(_tables[i] || '__view');
    _exec := 'CREATE OR REPLACE VIEW ' || quote_ident(_name) || ' AS SELECT ';
    _exec := _exec || (quote_ident('t' || i) || '.' || quote_ident(_keys[i])) || ' AS id, ';
    FOR i IN array_lower(_tables, 1)..array_upper(_tables, 1) LOOP
        FOR _rec in (
            SELECT a.attname from pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid WHERE c.relname=_tables[i] AND a.attnum > 0 ORDER BY a.attnum
        ) LOOP
            IF _rec.attname = '_version_transaction' THEN
                _vers := _vers || (quote_ident('t' || i) || '.' || quote_ident(_rec.attname));
            ELSIF _rec.attname <> _keys[i] THEN
                _cols := _cols || (quote_ident('t' || i) || '.' || quote_ident(_rec.attname));
            END IF;
        END LOOP;
    END LOOP;
    _exec := _exec || array_to_string(_cols, ', ');
    IF _vers <> ARRAY[]::TEXT[] THEN
        _exec := _exec || ', GREATEST(' || array_to_string(_vers, ', ') || ') AS _version_transaction';
    END IF;
    _exec := _exec || ' FROM ';
    j := array_lower(_tables, 1);
    _exec := _exec || quote_ident(_tables[j]) || ' ' || quote_ident('t' || j);
    FOR i IN (j+1)..array_upper(_tables, 1) LOOP
        _exec := _exec || ' LEFT JOIN ' || quote_ident(_tables[i]) || ' ' || quote_ident('t' || i);
        _exec := _exec || ' ON ' || quote_ident('t' || j) || '.' || quote_ident(_keys[j]) || ' = ' || quote_ident('t' || i) || '.' || quote_ident(_keys[i]);
    END LOOP;
    EXECUTE _exec;
    RETURN _exec;
END;
$$ LANGUAGE plpgsql;
"""
    create_version_function_function = """
CREATE OR REPLACE FUNCTION create_version_function(_tables TEXT[], _keys TEXT[]) RETURNS TEXT AS $$
DECLARE
    _exec TEXT := '';
    _texec TEXT := '';
    _name TEXT;
    _vtables TEXT[];
    _cols TEXT[];
    _vers TEXT[];
    _rec RECORD;
    i INTEGER;
    j INTEGER;
BEGIN
    i := array_lower(_tables, 1);
    _name := quote_ident(_tables[i] || '__version_view');
    FOR i IN array_lower(_tables, 1)..array_upper(_tables, 1) LOOP
        SELECT INTO j COUNT(*) FROM pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE c.relname=_tables[i] AND a.attnum > 0 AND a.attname = '_version_transaction';
        IF j > 0 THEN
            _exec := 'CREATE OR REPLACE FUNCTION ' || quote_ident(_tables[i] || '__version_id') || '(_id INTEGER, _ver INTEGER) RETURNS INTEGER AS ''';
            _exec := _exec || 'DECLARE _v INTEGER;';
            _exec := _exec || 'BEGIN SELECT INTO _v MAX(_version_transaction) FROM ' || quote_ident(_tables[i]) || '__versions';
            _exec := _exec || ' WHERE ' || quote_ident(_keys[i]) || '=_id AND _version_transaction<=_ver AND _version_next IS NULL OR _version_next>_ver;';
            _exec := _exec || 'RETURN _v; END; '' LANGUAGE plpgsql;';
            _texec := _texec || _exec || ';';
            EXECUTE _exec;
            _vtables := _vtables || (quote_ident(_tables[i] || '__versions'));
        ELSE
            _vtables := _vtables || (quote_ident(_tables[i]));
        END IF;
    END LOOP;

    _exec := 'CREATE OR REPLACE FUNCTION ' || quote_ident(_name) || '(_id INTEGER, _ver INTEGER) RETURNS TABLE(id integer';
    FOR i IN array_lower(_tables, 1)..array_upper(_tables, 1) LOOP
        FOR _rec in (
            SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS type from pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE c.relname=_tables[i] AND a.attnum > 0 ORDER BY a.attnum
        ) LOOP
            IF _rec.attname <> '_version_transaction' AND _rec.attname <> _keys[i] THEN
                _exec := _exec || ',' || quote_ident(_rec.attname) || ' ' || _rec.type;
            END IF;
        END LOOP;
    END LOOP;
    _exec := _exec || ', _version_transaction integer) AS ''';
    _exec := _exec || 'BEGIN RETURN QUERY SELECT ';
    i := array_lower(_tables, 1);
    _exec := _exec || (quote_ident('t' || i) || '.' || quote_ident(_keys[i])) || ', ';
    FOR i IN array_lower(_tables, 1)..array_upper(_tables, 1) LOOP
        FOR _rec in (
            SELECT a.attname from pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid WHERE c.relname=_tables[i] AND a.attnum > 0 ORDER BY a.attnum
        ) LOOP
            IF _rec.attname = '_version_transaction' THEN
                _vers := _vers || (quote_ident('t' || i) || '.' || quote_ident(_rec.attname));
            ELSIF _rec.attname <> _keys[i] THEN
                _cols := _cols || (quote_ident('t' || i) || '.' || quote_ident(_rec.attname));
            END IF;
        END LOOP;
    END LOOP;
    _exec := _exec || array_to_string(_cols, ', ');
    IF _vers <> ARRAY[]::TEXT[] THEN
        _exec := _exec || ', GREATEST(' || array_to_string(_vers, ', ') || ')';
    END IF;
    _exec := _exec || ' FROM ';
    j := array_lower(_tables, 1);
    _exec := _exec || _vtables[j] || ' ' || quote_ident('t' || j);
    FOR i IN (j+1)..array_upper(_tables, 1) LOOP
        _exec := _exec || ' LEFT JOIN ' || _vtables[i] || ' ' || quote_ident('t' || i);
        _exec := _exec || ' ON ' || quote_ident('t' || j) || '.' || quote_ident(_keys[j]) || ' = ' || quote_ident('t' || i) || '.' || quote_ident(_keys[i]);
    END LOOP;
    _exec := _exec || ' WHERE ' || quote_ident('t' || j) || '.' || quote_ident(_keys[j]) || ' = _id';
    FOR i IN array_lower(_tables, 1)..array_upper(_tables, 1) LOOP
        SELECT INTO j COUNT(*) FROM pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE c.relname=_tables[i] AND a.attnum > 0 AND a.attname = '_version_transaction';
        IF j > 0 THEN
            _exec := _exec || ' AND ' || quote_ident('t' || i) || '._version_transaction = ' || quote_ident(_tables[i] || '__version_id') || '(_id,_ver)';
        END IF;
    END LOOP;
    _exec := _exec || '; END; '' LANGUAGE plpgsql;';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    RETURN _texec;
END;
$$ LANGUAGE plpgsql;
"""

    create_triggers_function = """
CREATE OR REPLACE FUNCTION create_triggers(_table TEXT, _key TEXT, _notify TEXT) RETURNS TEXT AS $$
DECLARE
    _exec TEXT := '';
    _texec TEXT := '';
    _rec RECORD;
BEGIN
    _exec := 'CREATE OR REPLACE FUNCTION ' || quote_ident(_table || '__on_after_insert') || '() RETURNS TRIGGER AS $' || '$';
    _exec := _exec || 'BEGIN INSERT INTO ' || quote_ident(_table || '__versions') || '(';
    FOR _rec in (
        SELECT a.attname from pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid WHERE c.relname=_table AND a.attnum > 0 ORDER BY a.attnum
    ) LOOP
        IF _rec.attname <> '_version_transaction' THEN
            _exec := _exec || quote_ident(_rec.attname) || ', ';
        END IF;
    END LOOP;
    _exec := _exec || '_version_transaction, _version_prev, _version_user';
    _exec := _exec || ') VALUES(';
    FOR _rec in (
        SELECT a.attname from pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid WHERE c.relname=_table AND a.attnum > 0 ORDER BY a.attnum
    ) LOOP
        IF _rec.attname <> '_version_transaction' THEN
            _exec := _exec || 'new.' || quote_ident(_rec.attname) || ', ';
        END IF;
    END LOOP;
    _exec := _exec || 'get_transaction_id(), get_transaction_id(), get_user_id());';
    _exec := _exec || 'INSERT INTO core_notification(action, "table", object, transaction, previous, "user") VALUES(''I'', ''' || _table || ''', new.' || quote_ident(_key);
    _exec := _exec || ', get_transaction_id(), NULL, get_user_id());';
    _exec := _exec || 'NOTIFY ' || quote_ident(_notify) || ';';
    _exec := _exec || 'RETURN new; END; $' || '$ LANGUAGE plpgsql;';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    _exec := 'CREATE TRIGGER ' || quote_ident(_table || '__after_insert') || ' AFTER INSERT ON ';
    _exec := _exec || quote_ident(_table) || ' FOR EACH ROW EXECUTE PROCEDURE ' || quote_ident(_table || '__on_after_insert') || '();';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;

    _exec := 'CREATE OR REPLACE FUNCTION ' || quote_ident(_table || '__on_before_update') || '() RETURNS TRIGGER AS $' || '$';
    _exec := _exec || 'BEGIN IF old <> new THEN new._version_transaction = get_transaction_id(); END IF; RETURN new; END; $' || '$ LANGUAGE plpgsql;';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    _exec := 'CREATE TRIGGER ' || quote_ident(_table || '__before_update') || ' BEFORE UPDATE ON ';
    _exec := _exec || quote_ident(_table) || ' FOR EACH ROW EXECUTE PROCEDURE ' || quote_ident(_table || '__on_before_update') || '();';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;

    _exec := 'CREATE OR REPLACE FUNCTION ' || quote_ident(_table || '__on_after_update') || '() RETURNS TRIGGER AS $' || '$';
    _exec := _exec || 'BEGIN IF old = new THEN return new; END IF;';
    _exec := _exec || 'UPDATE ' || quote_ident(_table || '__versions') || ' SET _version_next = get_transaction_id() WHERE ';
    _exec := _exec || quote_ident(_key) || ' = new.' || quote_ident(_key) || ' AND _version_next IS NULL;';
    _exec := _exec || 'DELETE FROM ' || quote_ident(_table || '__versions') || ' WHERE _version_transaction = get_transaction_id() AND ';
    _exec := _exec || quote_ident(_key) || ' = new.' || quote_ident(_key) || ';';
    _exec := _exec || 'INSERT INTO ' || quote_ident(_table || '__versions') || '(';
    FOR _rec in (
        SELECT a.attname from pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid WHERE c.relname=_table AND a.attnum > 0 ORDER BY a.attnum
    ) LOOP
        IF _rec.attname <> '_version_transaction' THEN
            _exec := _exec || quote_ident(_rec.attname) || ', ';
        END IF;
    END LOOP;
    _exec := _exec || '_version_transaction, _version_prev, _version_user';
    _exec := _exec || ') VALUES(';
    FOR _rec in (
        SELECT a.attname from pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid WHERE c.relname=_table AND a.attnum > 0 ORDER BY a.attnum
    ) LOOP
        IF _rec.attname <> '_version_transaction' THEN
            _exec := _exec || 'new.' || quote_ident(_rec.attname) || ', ';
        END IF;
    END LOOP;
    _exec := _exec || 'get_transaction_id(), old._version_transaction, get_user_id());';
    _exec := _exec || 'UPDATE core_notification SET "user"=get_user_id() WHERE "table"=''' || _table || ''' AND object=new.' || quote_ident(_key);
    _exec := _exec || ' AND transaction=get_transaction_id(); IF NOT found THEN ';
    _exec := _exec || 'INSERT INTO core_notification(action, "table", object, transaction, previous, "user") VALUES(''U'', ''' || _table || ''', new.' || quote_ident(_key);
    _exec := _exec || ', get_transaction_id(), old._version_transaction, get_user_id()); END IF;';
    _exec := _exec || 'NOTIFY ' || quote_ident(_notify) || ';';
    _exec := _exec || 'RETURN new; END; $' || '$ LANGUAGE plpgsql;';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    _exec := 'CREATE TRIGGER ' || quote_ident(_table || '__after_update') || ' AFTER UPDATE ON ';
    _exec := _exec || quote_ident(_table) || ' FOR EACH ROW EXECUTE PROCEDURE ' || quote_ident(_table || '__on_after_update') || '();';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;

    _exec := 'CREATE OR REPLACE FUNCTION ' || quote_ident(_table || '__on_after_delete') || '() RETURNS TRIGGER AS $' || '$';
    _exec := _exec || 'BEGIN UPDATE ' || quote_ident(_table || '__versions') || ' SET _version_next = get_transaction_id() WHERE ';
    _exec := _exec || quote_ident(_key) || ' = old.' || quote_ident(_key) || ' AND _version_next IS NULL;';
    _exec := _exec || 'DELETE FROM ' || quote_ident(_table || '__versions') || ' WHERE _version_transaction = get_transaction_id() AND ';
    _exec := _exec || quote_ident(_key) || ' = old.' || quote_ident(_key) || ';';
    _exec := _exec || 'UPDATE core_notification SET action=''D'', "user"=get_user_id() WHERE "table"=''' || _table || ''' AND object=old.' || quote_ident(_key);
    _exec := _exec || ' AND transaction=get_transaction_id(); IF NOT found THEN ';
    _exec := _exec || 'INSERT INTO core_notification(action, "table", object, transaction, previous, "user") VALUES(''D'', ''' || _table || ''', old.' || quote_ident(_key);
    _exec := _exec || ', get_transaction_id(), old._version_transaction, get_user_id()); END IF;';
    _exec := _exec || 'NOTIFY ' || quote_ident(_notify) || ';';
    _exec := _exec || 'RETURN old; END; $' || '$ LANGUAGE plpgsql;';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    _exec := 'CREATE TRIGGER ' || quote_ident(_table || '__after_delete') || ' AFTER DELETE ON ';
    _exec := _exec || quote_ident(_table) || ' FOR EACH ROW EXECUTE PROCEDURE ' || quote_ident(_table || '__on_after_delete') || '();';
    _texec := _texec || _exec || ';';
    EXECUTE _exec;
    RETURN _texec;
END;
$$ LANGUAGE plpgsql;
"""

    install_rights_inheritance = """
DROP TABLE IF EXISTS "right_dict";
CREATE TABLE "right_dict" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" VARCHAR(32),
    UNIQUE("name")
);
CREATE OR REPLACE FUNCTION get_right_by_name(_right_name TEXT) RETURNS INT AS $$
DECLARE
    _ret INT := NULL;
BEGIN
    _ret := (SELECT "id" FROM "right_dict" WHERE "name" = _right_name);
    IF _ret IS NULL THEN
        INSERT INTO right_dict("name") VALUES(_right_name);
        _ret := (SELECT "id" FROM "right_dict" WHERE "name" = _right_name);
    END IF;
    RETURN _ret;
END;
$$ LANGUAGE plpgsql;
CREATE TYPE "right_pair" AS (
    "entity_id" INT,
    "right_id"  INT
);
DROP TABLE IF EXISTS "right_inheritance";
CREATE TABLE "right_inheritance" (
    "parent" INT NOT NULL,
    "child" INT NOT NULL,
    "child_entity_id" INT NOT NULL
);
CREATE INDEX "right_inheritance_child_idx" ON "right_inheritance" ( "child" );
CREATE INDEX "right_inheritance_child_entity_id_idx" ON "right_inheritance" ( "child_entity_id" );
CREATE OR REPLACE FUNCTION right_inheritance_clear(_entity_id INT) RETURNS VOID AS $$
BEGIN
    DELETE FROM "right_inheritance" WHERE "child_entity_id" = _entity_id;
END;
$$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION right_inheritance_add(_child_entity_id INT, _child_right_name TEXT, _parent_entity_id INT, _parent_right_name TEXT) RETURNS VOID AS $$
BEGIN
    IF _child_entity_id IS NULL OR _child_right_name IS NULL OR _parent_entity_id IS NULL OR _parent_right_name IS NULL THEN
        RETURN;
    END IF;
    INSERT INTO "right_inheritance"("parent", "child", "child_entity_id") VALUES (
        _parent_entity_id*256 + (SELECT get_right_by_name(_parent_right_name)),
        _child_entity_id*256 + (SELECT get_right_by_name(_child_right_name)),
        _child_entity_id);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION right_check(_entity_id INT, _right_name TEXT) RETURNS BOOLEAN AS $$
DECLARE result BOOLEAN;
BEGIN
   SELECT EXISTS
       (SELECT * FROM
           user_roles
           JOIN core_privilege ON user_roles.role_id = core_privilege.role_id
           JOIN right_dict ON core_privilege.right = right_dict.name
           JOIN
           (SELECT keyid/256 as entity, keyid%256 as right 
                FROM connectby('right_inheritance'::text, 'parent'::text, 'child'::text, (_entity_id*256 + (SELECT get_right_by_name(_right_name)))::text, 0)
                AS t(keyid int, parent_keyid int, level int)
           ) AS inherited ON inherited.right = right_dict.id AND core_privilege.entity_id = inherited.entity
           WHERE coalesce(core_privilege.start_on, NOW()) <= NOW() AND coalesce(core_privilege.finish_on, NOW()) >= NOW()
       )
       INTO result;
   RETURN result;
EXCEPTION
    WHEN undefined_table THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;
"""

    install_versions_function = """
CREATE OR REPLACE FUNCTION install_versions(_table TEXT, _key TEXT, _tables TEXT[], _keys TEXT[], _notify TEXT) RETURNS TEXT AS $$
DECLARE
    _texec TEXT := '';
    _exec TEXT := '';
BEGIN
    SELECT INTO _exec create_version_table(_table, _key);
    _texec := _texec || _exec;
    SELECT INTO _exec create_full_view(_tables, _keys);
    _texec := _texec || _exec;
    SELECT INTO _exec create_version_function(_tables, _keys);
    _texec := _texec || _exec;
    SELECT INTO _exec create_triggers(_table, _key, _notify);
    _texec := _texec || _exec;
    RETURN _texec;
END;
$$ LANGUAGE plpgsql;
"""
    ret = [set_user_id_function, get_user_id_function, transaction_id_seq, get_transaction_id_function, insert_rawevent_trigger, create_version_table_function, create_full_view_function, create_version_function_function, create_triggers_function, install_versions_function, install_rights_inheritance]
    for model in sorted(registry.keys(), key=lambda m: m._meta.db_table):
        ret.append(install_versions_sql(model))
    return tuple(ret);
