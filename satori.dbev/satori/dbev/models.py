# vim:ts=4:sts=4:sw=4:expandtab
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import models

class UserField(models.IntegerField):
    def __init__(self):
        super(UserField, self).__init__(self, blank = True, null = True)

    def post_create_sql(self, style, db_table):
        create_language = ''
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

        return (create_language, set_user_id_function, get_user_id_function, transaction_id_seq, get_transaction_id_function)


class Notification(models.Model):
    notification = 'satori'
    action      = models.CharField(max_length=1)
    model       = models.CharField(max_length=50)
    object      = models.IntegerField()
    transaction = models.IntegerField()
    entry       = models.IntegerField(null=True, blank=True)
    user        = UserField()
