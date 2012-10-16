# vim:ts=4:sts=4:sw=4:expandtab

from collections import deque
import logging
from multiprocessing import Process
import os
import shutil
import subprocess
import tempfile

from satori.core.models import *
from satori.events import Event, Client2

serial = 1

def printer_func(script, path, filename):
    tmp = None
    try:
        tmp = tempfile.mkdtemp()
        os.chdir(tmp)
        os.symlink(path, filename)
        subprocess.call([script, filename])
    finally:
        if(tmp is not None):
            shutil.rmtree(tmp)

class PrintingMaster(Client2):
    queue = 'printing_master_queue'

    def __init__(self):
        super(PrintingMaster, self).__init__()
        self.printjob_queue = deque()

    def init(self):
        self.attach(self.queue)
        self.map({'type': 'printjob'}, self.queue)
        self.do_work()

    def do_work(self):
        while len(self.printjob_queue) > 0:
            printjob = self.printjob_queue.pop();
            self.do_printjob(printjob)

    def handle_event(self, queue, event):
        logging.debug('checking master: event %s', event.type)
        if event.type == 'printjob':
            printjob = PrintJob.objects.get(id=event.id)
            self.printjob_queue.append(printjob)
        self.do_work()

    def do_printjob(self, printjob):
        printer = printjob.contest.printer;
        if (printer is not None):
            oa = printjob.data_get('content');
            path = os.path.join(settings.BLOB_DIR, oa.value[0], oa.value[1], oa.value[2], oa.value)
            p=Process(target=printer_func, args=(printer.script, path, oa.filename))
            p.daemon=True
            p.start()
