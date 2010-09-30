# vim:ts=4:sts=4:sw=4:expandtab

import time

_total = {}
_begin = {}

def begin(name):
    _begin[name] = time.time()

def end(name):
    if not name in _begin:
        raise Exception("Name not in _begin")

    diff = time.time() - _begin[name]
    del _begin[name]

    _total[name] = _total.get(name, 0) + diff

    print 'End:\t{0}\t{1}\t{2}'.format(name, diff, _total[name])

def clear(name):
    if name in _total:
        del _total[name]

