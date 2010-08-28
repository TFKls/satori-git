# vim:ts=4:sts=4:sw=4:expandtab
import os, re

requestDir = os.path.dirname(__file__)
files = os.listdir(requestDir)

for fname in files:
    m = re.match('^_([a-zA-Z]*)\.py$', fname)
    if m:
        reqName = m.group(1)
        todo = 'from _{0} import {0}'.format(reqName)
        exec todo

from _Request import process
