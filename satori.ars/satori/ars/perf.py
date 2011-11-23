# vim:ts=4:sts=4:sw=4:expandtab

import logging
import threading
import time

class X(threading.local):
    def __init__(self):
        self._total = {}
        self._begin = {}
        self._count = {}

x = X()

def begin(name):
    x._begin[name] = time.time()

def end(name):
    if not name in x._begin:
        raise Exception("Name not in _begin")

    diff = time.time() - x._begin[name]
    del x._begin[name]

    x._total[name] = x._total.get(name, 0) + diff
    x._count[name] = x._count.get(name, 0) + 1

    logging.debug('End:\t%s\t%s\t%s\t%s', name, '{0:.3f}'.format(diff), '{0:.3f}'.format(x._total[name]), x._count[name])

def clear(name):
    x._total = {}
    self._count = {}

