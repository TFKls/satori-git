import os, re

widgetDir = os.path.dirname(__file__)
files = os.listdir(widgetDir)

for fname in files:
    m = re.match('^_([a-zA-Z]*)\.py$', fname)
    if m:
        widName = m.group(1)
        todo = 'from _{0} import {0}'.format(widName)
        exec todo
