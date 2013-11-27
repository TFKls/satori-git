# vim:ts=4:sts=4:sw=4:expandtab

from collections import deque
import logging
from multiprocessing import Process
from threading import Thread
import os
import shutil
import subprocess
import tempfile

from satori.core.models import *
from satori.events import Event, Client2

#TODO: Launch no more than n jobs simultaneously

def printer_func(script, path, filename, printjob):
    tmp = None
    try:
        tmp = tempfile.mkdtemp()
        os.chdir(tmp)
        shutil.copy(path, filename)
        sub = subprocess.Popen([script, filename, unicode(printjob.id)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sub.communicate()
        if sub.returncode == 0:
            RawEvent().send(Event(type='printjob_done', id = printjob.id, status = 'OK', report = out[0:200]))
        else:
            RawEvent().send(Event(type='printjob_done', id = printjob.id, status = 'FAIL', report = (err+out)[0:200]))
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
        self.map({'type': 'printjob_new'}, self.queue)
        self.map({'type': 'printjob_done'}, self.queue)
        for printjob in PrintJob.objects.filter(pending=True):
            printjob.status = 'QUE'
            printjob.report = ''
            printjob.save()
            self.printjob_queue.append(printjob)
        self.do_work()

    def do_work(self):
        while len(self.printjob_queue) > 0:
            printjob = self.printjob_queue.pop();
            self.do_printjob(printjob)

    def handle_event(self, queue, event):
        logging.debug('checking master: event %s', event.type)
        if event.type == 'printjob_new':
            printjob = PrintJob.objects.get(id=event.id)
            printjob.status = 'QUE'
            printjob.report = ''
            printjob.save()
            self.printjob_queue.append(printjob)
        elif event.type == 'printjob_done':
            printjob = PrintJob.objects.get(id=event.id)
            printjob.pending = False
            printjob.status = event.status
            printjob.report = event.report
            printjob.save()
        self.do_work()

    def do_printjob(self, printjob):
        printer = printjob.contest.printer;
        if (printer is not None):
            oa = printjob.data_get('content');
            path = os.path.abspath(os.path.join(settings.BLOB_DIR, oa.value[0], oa.value[1], oa.value[2], oa.value))
            p = Thread(target=printer_func, args=(printer.script, path, oa.filename, printjob))
            printjob.status = 'PRN'
            printjob.save()
            p.daemon = True
            p.start()
