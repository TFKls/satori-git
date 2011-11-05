# vim:ts=4:sts=4:sw=4:expandtab

from   django.db import connection
import threading

from satori.core.export.type_helpers import DefineException


TokenExpired = DefineException('TokenExpired', 'The provided token has expired')
TokenInvalid = DefineException('TokenInvalid', 'The provided token is invalid')


class TokenContainer(threading.local):
    def __init__(self):
        self.token = None

    def check_set_token_str(self, token_str):
        try:
            token = Token(token_str)
        except:
            raise TokenInvalid()

        if not token.valid:
            raise TokenExpired()

        self.set_token(token)

    def set_token(self, token):
        self.token = token

        contest = Contest.get_current_lock()
        if contest:
            if token.role:
                contestant = contest.find_contestant(token.role)
                if not contestant:
                    raise TokenInvalid()
                userid = int(contestant.id)
            else:
                userid = Global.get_instance().zero.id
        else:
            if token.role:
                userid = int(token.role.id)
            else:
                userid = Global.get_instance().anonymous.id

        cursor = connection.cursor()
        cursor.callproc('set_user_id', [userid])
        cursor.close()



token_container = TokenContainer()


def init():
    global Contest
    global Global
    global Token
    from satori.core.models import Global, Contest
    from satori.core.sec.token import Token
