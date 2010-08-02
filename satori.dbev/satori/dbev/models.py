# vim:ts=4:sts=4:sw=4:expandtab
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import models

class UserField(models.IntegerField):
    def __init__(self):
        super(UserField, self).__init__(self, blank = True, null = True)

    def post_create_sql(self, style, db_table):
        set_user_id_function = """
CREATE OR REPLACE FUNCTION set_user_id(arg INTEGER) RETURNS VOID AS $$
BEGIN
    UPDATE user_id SET id=arg;
EXCEPTION
    WHEN undefined_table THEN
        CREATE TEMPORARY TABLE user_id (id INTEGER);
    INSERT INTO user_id VALUES (arg);
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
        repair_version_table_function = """
CREATE OR REPLACE FUNCTION repair_version_table(name TEXT) RETURNS INTEGER AS $$
DECLARE
    con RECORD;
    count INTEGER;
BEGIN
    count = 0;
    FOR con in (SELECT constraint_name FROM information_schema.table_constraints WHERE table_name=name and constraint_type='UNIQUE') LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(name) || ' DROP CONSTRAINT ' || quote_ident(con.constraint_name);
        count = count + 1;
    END LOOP;
    RETURN count;
END;
$$ LANGUAGE plpgsql;
"""
        create_full_view_function = """
CREATE OR REPLACE FUNCTION create_full_view(_name TEXT, _tables TEXT[], _keys TEXT[]) RETURNS TEXT AS $$
DECLARE
    _exec TEXT;
    _cols TEXT[];
    _vers TEXT[];
    _rec RECORD;
    i INTEGER;
    j INTEGER;
BEGIN
    _exec := 'CREATE OR REPLACE VIEW ' || quote_ident(_name) || ' AS SELECT ';
    i := array_lower(_tables, 1);
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
CREATE OR REPLACE FUNCTION create_version_function(_name TEXT, _tables TEXT[], _keys TEXT[]) RETURNS TEXT AS $$
DECLARE
    _exec TEXT;
    _vtables TEXT[];
    _cols TEXT[];
    _vers TEXT[];
    _rec RECORD;
    i INTEGER;
    j INTEGER;
BEGIN
    _exec = '';
    FOR i IN array_lower(_tables, 1)..array_upper(_tables, 1) LOOP
        SELECT INTO j COUNT(*) FROM pg_class c LEFT JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE c.relname=_tables[i] AND a.attnum > 0 AND a.attname = '_version_transaction';
        IF j > 0 THEN
            _exec := _exec || 'CREATE OR REPLACE FUNCTION ' || quote_ident(_tables[i] || '_tableversion') || '(_id INTEGER, _ver INTEGER) RETURNS INTEGER AS ''';
            _exec := _exec || 'DECLARE _v INTEGER;';
            _exec := _exec || 'BEGIN SELECT INTO _v MAX(_version_transaction) FROM ' || quote_ident(_tables[i]) || '__versions';
            _exec := _exec || ' WHERE ' || quote_ident(_keys[i]) || '=_id AND _version_transaction<=_ver;';
            _exec := _exec || 'RETURN _v; END; '' LANGUAGE plpgsql;';
            EXECUTE _exec;
            _exec := '';
            _vtables := _vtables || (quote_ident(_tables[i] || '__versions'));
        ELSE
            _vtables := _vtables || (quote_ident(_tables[i]));
        END IF;
    END LOOP;

    _exec := _exec || 'CREATE OR REPLACE FUNCTION ' || quote_ident(_name) || '(_id INTEGER, _ver INTEGER) RETURNS TABLE(id integer';
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
            _exec := _exec || ' AND ' || quote_ident('t' || i) || '._version_transaction = ' || quote_ident(_tables[i] || '_tableversion') || '(_id,_ver)';
        END IF;
    END LOOP;
    _exec := _exec || '; END; '' LANGUAGE plpgsql;';
    EXECUTE _exec;
    RETURN _exec;
END;
$$ LANGUAGE plpgsql;
"""


        return (set_user_id_function, get_user_id_function, transaction_id_seq, get_transaction_id_function, repair_version_table_function, create_full_view_function, create_version_function_function)


class Notification(models.Model):
    notification = 'satori'
    action      = models.CharField(max_length=1)
    table       = models.CharField(max_length=50)
    object      = models.IntegerField()
    transaction = models.IntegerField()
    entry       = models.IntegerField(null=True, blank=True)
    user        = UserField()
