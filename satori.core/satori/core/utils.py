# vim:ts=4:sts=4:sw=4:expandtab

import os

def ensuredirs(path, mode=0777):
    try:
        os.makedirs(path, mode)
    except OSError:
        if not os.path.isdir(path):
            raise
