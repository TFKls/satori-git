# vim:ts=4:sts=4:sw=4:expandtab

import logging
import os
import shutil
import sys

from satori.client.common import want_import
want_import(globals(), '*')

def default_judges():
    from satori.tools import options, setup
    (options, args) = setup()
    if len(args) != 1:
        logging.error('incorrect number of arguments')
        sys.exit(1)
    judges_dir = unicode(args[0])
    for judge in [ os.path.join(judges_dir, entry) for entry in os.listdir(judges_dir) if os.path.isfile(os.path.join(judges_dir, entry)) ]:
        if judge[-3:] == '.py':
            name = os.path.basename(judge)[:-3]
            blob = Global.get_instance().judges_set_blob_path(name, judge)
