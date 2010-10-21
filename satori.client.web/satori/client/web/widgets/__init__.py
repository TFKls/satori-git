import os, re
import traceback

widgetDir = os.path.dirname(__file__)
files = os.listdir(widgetDir)

for fname in files:
    print fname
    m = re.match(r'^_([a-zA-Z]*)\.py$', fname)
    if m:
        widName = m.group(1)
        print widName
        todo = 'from _{0} import {0}'.format(widName)
        try:
            exec todo
        except:
            print 'Error importing module:'
            traceback.print_exc()
            raise
