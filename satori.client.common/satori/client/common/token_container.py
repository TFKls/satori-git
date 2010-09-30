# vim:ts=4:sts=4:sw=4:expandtab

import threading

class TokenContainer(threading.local):
    def __init__(self):
        self._token = ""

    def set_token(self, token):
        self._token = token

    def unset_token(self):
        self._token = ""

    def get_token(self):
        return self._token

token_container = TokenContainer()

