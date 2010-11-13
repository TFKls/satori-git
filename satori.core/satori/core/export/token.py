# vim:ts=4:sts=4:sw=4:expandtab

from   django.db import connection
import threading


class TokenContainer(threading.local):
    def __init__(self):
        self.token = None

    def set_token(self, token):
        if isinstance(token, (str, unicode)):
            token = Token(token)

        self.token = token

        if token.user_id:
            userid = int(token.user_id)
        else:
            userid = Global.get_instance().anonymous.id

        cursor = connection.cursor()
        cursor.callproc('set_user_id', [userid])
        cursor.close()


token_container = TokenContainer()


def init():
    global Global
    global Token
    from satori.core.models import Global
    from satori.core.sec import Token
