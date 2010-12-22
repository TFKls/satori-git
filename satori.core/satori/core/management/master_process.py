# vim:ts=4:sts=4:sw=4:expandtab

from   django.conf     import settings
import errno
import fcntl
import logging
from   multiprocessing import Process, Semaphore
import sys
import os
from   setproctitle import setproctitle
from   signal       import signal, getsignal, SIGINT, SIGTERM, SIGHUP, pause
import signal       as signal_module
from   time         import sleep


signalnames = dict((k, v) for v, k in signal_module.__dict__.iteritems() if v.startswith('SIG'))


class SatoriProcess(Process):
    def __init__(self, name):
        super(SatoriProcess, self).__init__()
        self.name = name
    
    def join(self, timeout=None):
        while True:
            try:
                super(SatoriProcess, self).join(timeout)
                break;
            except OSError as e:
                if e[0] != errno.EINTR:
                    raise

    def do_handle_signal(self, signum, frame):
        sys.exit()

    def handle_signal(self, signum, frame):
        logging.info('%s caught signal %s', self.name, signalnames.get(signum, signum))
        self.do_handle_signal(signum, frame)

    def run(self):
        setproctitle('satori: {0}'.format(self.name))

        signal(SIGTERM, self.handle_signal)
        signal(SIGINT, self.handle_signal)
        signal(SIGHUP, self.handle_signal)

        logging.info('%s starting', self.name)

        try:
            self.do_run()
        except:
            logging.exception('%s exited with error', self.name)
        else:
            logging.info('%s exited', self.name)


class SatoriMasterProcess(SatoriProcess):
    def __init__(self, is_daemon):
        super(SatoriMasterProcess, self).__init__('master')
        self.name = 'master'
        self.is_daemon = is_daemon
        self.sem = Semaphore(0)
    
    def do_handle_signal(self, signum, frame):
        for process in reversed(self.started):
            process.terminate()
            # wait for each child so it can deinitialize while other processes (like event master) still exist
            process.join()

    def do_run(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            logger.removeHandler(handler)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        fp = open(settings.PID_FILE, 'a+')

        try:
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            fp.close()
            raise RuntimeError('Satori already running')

        fp.seek(0)
        fp.truncate()
        fp.write(str(os.getpid()))
        fp.flush()

        os.chdir('/') 
        os.umask(0) 
        os.setsid()

        logging.info('Loading ARS interface...')
        import satori.core.api
        logging.info('ARS interface loaded.')

        if self.is_daemon:
            logger.removeHandler(console_handler)
            
            os.close(sys.stdin.fileno())
            os.open('/dev/null', os.O_RDWR)
            os.close(sys.stdout.fileno())
            os.open('/dev/null', os.O_RDWR)
            os.close(sys.stderr.fileno())
            os.open('/dev/null', os.O_RDWR)
        
        self.sem.release()

        from satori.core.management.processes import EventMasterProcess, DbevNotifierProcess, ThriftServerProcess, BlobServerProcess, DebugQueueProcess, CheckQueueProcess, DispatcherRunnerProcess

        to_start = [
                EventMasterProcess(),
                DebugQueueProcess(),
                DbevNotifierProcess(),
                CheckQueueProcess(),
                DispatcherRunnerProcess(),
                ThriftServerProcess(),
                BlobServerProcess(),
        ]

        self.started = []

        for process in to_start:
            process.start()
            self.started.append(process)

        for process in reversed(self.started):
            process.join()

        fp.close()
        os.remove(settings.PID_FILE)

    def start(self, *args, **kwargs):
        super(SatoriMasterProcess, self).start(*args, **kwargs)
        while True:
            if self.sem.acquire(False):
                return
            if not self.is_alive():
                raise RuntimeError('Satori master failed to start')
            sleep(0)

    def stop(self):
        fp = open(settings.PID_FILE, 'a+')
        try:
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            fp.seek(0)
            pid = int(fp.read())
            fp.close()
            os.kill(pid, SIGINT)
        else:
            fp.close()
            print 'Satori not running'



