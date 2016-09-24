# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab
"""Satori judge implementation.
"""

from satori.objects import Object, Argument
from satori.client.common import want_import
want_import(globals(), '*')
from types import NoneType
import BaseHTTPServer
import cgi
import datetime
from multiprocessing import Process, Pipe, Manager
import os
import sys
import shutil
import signal
import subprocess
import time
import unshare
import yaml
import traceback

def jailPath(root, path):
    return os.path.join(root, os.path.abspath(os.path.join('/',path))[1:])

class JailExec(Object):
    @Argument('root', type=str)
    @Argument('path', type=str)
    @Argument('args', default=[])
    @Argument('search', type=bool, default=False)
    def __init__(self, root, path, args, search):
        self.root = root
        self.path = path
        self.args = [self.path] + args
        self.search = search

    def run(self):
        os.chroot(self.root)
        os.chdir('/')
        if self.search:
            os.execvp(self.path, self.args)
        else:
            os.execv(self.path, self.args)

class JailBuilder(Object):
    scriptTimeout = 15

    @Argument('root', type=str)
    @Argument('template_path', type=str)
    @Argument('template', type=str)
    def __init__(self, root, template, template_path):
        template = os.path.split(template)[1]
        self.root = root
        self.jail_path = os.path.abspath(os.path.join(self.root, '__jail__'))
        self.template = os.path.join(template_path, template + '.template')

    def create(self):
        try:
            os.mkdir(self.root)
            subprocess.check_call(['mount', '-t', 'tmpfs', '-o', 'noatime,rw,size=1m', 'tmpfs', self.root])
            template = yaml.load(open(self.template, 'r'))
            dirlist = []
            quota = 0
            num = 1
            if 'base' in template:
                for base in template['base']:
                    if isinstance(base, str):
                        base = { 'path' : base }
                    opts = base.get('opts', '')
                    name = base.get('name', '__' + str(num) + '__')
                    num += 1
                    path = os.path.join(self.root, os.path.basename(name))
                    if 'path' in base:
                        type = base.get('type')
                        src = os.path.realpath(base['path'])
                        if os.path.isdir(src):
                            os.mkdir(path)
                            subprocess.check_call(['mount', '-o', 'bind,ro,'+opts, src, path])
                            dirlist.append((path,'ro'))
                        elif os.path.isfile(src):
                            os.mkdir(path)
                            if type is None:
                                ext = os.path.splitext(src)[1]
                                if ext:
                                    type = ext[1:]
                                else:
                                    type = 'auto'
                            subprocess.check_call(['mount', '-t', type, '-o', 'loop,noatime,ro,'+opts, src, path])
                            dirlist.append((path,'ro'))
                        else:
                          raise Exception('Path '+base['path']+' can\'t be mounted')
            if 'quota' in template:
                quota = int(template['quota'])
            if quota > 0:
                path = os.path.join(self.root, '__rw__')
                os.mkdir(path)
                subprocess.check_call(['mount', '-t', 'tmpfs', '-o', 'noatime,rw,size=' + str(quota) + 'm', 'tmpfs', path])
                dirlist.append((path,'rw'))
            os.mkdir(self.jail_path)
            unionfs = 'overlayfs'
            if len(dirlist) == 1:
                subprocess.check_call(['mount', '-o', 'bind', dirlist[0][0], self.jail_path])
            else:
                if unionfs == 'overlayfs':
                    if dirlist[-1][1] == 'rw':
                        ud = os.path.join(dirlist[-1][0],'ud')
                        wd = os.path.join(dirlist[-1][0],'wd')
                        os.mkdir(ud);
                        os.mkdir(wd);
                        subprocess.check_call(['mount', '-t', 'overlayfs', '-o', 'lowerdir='+ ':'.join([d[0] for d in reversed(dirlist[:-1])])+',upperdir='+ud+',workdir='+wd, 'overlayfs', self.jail_path])
                    else:
                        subprocess.check_call(['mount', '-t', 'overlayfs', '-o', 'lowerdir='+ ':'.join([d[0] for d in reversed(dirlist)]), 'overlayfs', self.jail_path])
                else:
                    subprocess.check_call(['mount', '-t', 'aufs', '-o', 'noatime,rw,dirs=' + ':'.join([d[0]+'='+d[1] for d in reversed(dirlist)]), 'aufs', self.jail_path])
            if 'insert' in template:
                for src in template['insert']:
                    src = os.path.realpath(src)
                    if os.path.isdir(src):
                        subprocess.check_call(['rsync', '-a', src, self.jail_path])
                    elif os.path.isfile(src):
                        name = os.path.basename(src).split('.')
                        if name[-1] == 'zip':
                            subprocess.check_call(['unzip', '-d', self.jail_path, src])
                        elif name[-1] == 'tar':
                            subprocess.check_call(['tar', '-C', self.jail_path, '-x', '-f', src])
                        elif name[-1] == 'tbz' or name[-1] == 'tbz2' or (name[-1] == 'bz' or name[-1] == 'bz2') and name[-2] == 'tar':
                            subprocess.check_call(['tar', '-C', self.jail_path, '-x', '-j', '-f', src])
                        elif name[-1] == 'tgz'  or name[-1] == 'gz' and name[-2] == 'tar':
                            subprocess.check_call(['tar', '-C', self.jail_path, '-x', '-z', '-f', src])
                        elif name[-1] == 'lzma' and name[-2] == 'tar':
                            subprocess.check_call(['tar', '-C', self.jail_path, '-x', '--lzma', '-f', src])
                        else:
                          raise Exception('Path '+src+ ' can\'t be inserted')
                    else:
                        raise Exception('Path '+src+ ' can\'t be inserted')
            if 'copy' in template:
                for copy in template['copy']:
                    if isinstance(copy, str):
                        copy = { 'src' : copy }
                    src = copy['src']
                    dst = jailPath(self.jail_path, copy.get('dst', src))
                    with open(src, "r") as s:
                        with open(dst, "w") as d:
                            shutil.copyfileobj(s, d)
                    st = os.stat(src)
                    os.chmod(dst, st.st_mode)
                    os.chown(dst, st.st_uid, st.st_gid)
            if 'remove' in template:
                for path in template['remove']:
                  subprocess.check_call(['rm', '-rf', jailPath(self.jail_path, path)])
            if 'bind' in template:
                for bind in template['bind']:
                    if isinstance(bind, str):
                        bind = { 'src' : bind }
                    src = bind['src']
                    dst = jailPath(self.jail_path, bind.get('dst', src))
                    opts = bind.get('opts', '')
                    rec = bind.get('recursive', 0)
                    if rec:
                        rec = 'rbind'
                    else:
                        rec = 'bind'
                    subprocess.check_call(['mount', '-o', rec + ',' + opts, src, dst])
            if 'script' in template:
                for script in template['script']:
                    params = script.split(' ')
                    runner = JailExec(root=self.jail_path, path=params[0], args=params[1:], search=True)
                    process = Process(target=runner.run)
                    process.start()
                    process.join(self.scriptTimeout)
                    if process.is_alive():
                        process.terminate()
                        raise Exception('Script '+script+' failed to finish before timeout')
                    if process.exitcode != 0:
                        raise Exception('Script '+script+' returned '+str(process.exitcode))
        except:
            self.destroy()
            raise

    def destroy(self):
        subprocess.call(['umount', '-l', self.root])
        os.rmdir(self.root)


class JailRun(Object):

    @Argument('root', type=str)
    @Argument('cgroup_path', type=str)
    @Argument('template_path', type=str)
    @Argument('path', type=str)
    @Argument('args', default=[])
    @Argument('runner_args', default=[])
    @Argument('host_eth', type=str)
    @Argument('host_ip', type=str)
    @Argument('guest_eth', type=str)
    @Argument('guest_ip', type=str)
    @Argument('netmask', type=str)
    @Argument('control_port', type=int)
    @Argument('cgroup', type=str, default='runner')
    @Argument('cgroup_memory', type=int, default=64*1024*1024)
    @Argument('real_time', type=int, default=5*60*1000)
    @Argument('debug', type=str, default='')
    @Argument('search', type=bool, default=False)
    def __init__(self, submit, root, cgroup_path, template_path, path, runner_args, args, host_eth, host_ip, guest_eth, guest_ip, netmask, control_port, cgroup, cgroup_memory, real_time, debug, search):
        self.submit = submit
        self.root = root
        self.cgroup_path = cgroup_path
        self.template_path = template_path
        self.path = path
        self.runner_args = runner_args
        self.args = [self.path] + args
        self.host_eth = host_eth
        self.host_ip = host_ip
        self.guest_eth = guest_eth
        self.guest_ip = guest_ip
        self.netmask = netmask
        self.control_port = control_port
        self.cgroup = cgroup
        self.cgroup_memory = cgroup_memory
        self.real_time = real_time
        self.debug = debug
        self.search = search

    def child(self, pipe):
        try:
            unshare.unshare(unshare.CLONE_NEWNS | unshare.CLONE_NEWUTS | unshare.CLONE_NEWIPC | unshare.CLONE_NEWNET)

            pipe.send(1)
#WAIT FOR PARENT CREATE CONTROLLER
            pipe.recv()
            subprocess.check_call(['ifconfig', self.guest_eth, self.guest_ip, 'netmask', self.netmask, 'up'])
            subprocess.check_call(['route', 'add', 'default', 'gw', self.host_ip])
            subprocess.check_call(['ifconfig', 'lo', '127.0.0.1/8', 'up'])
            subprocess.check_call(['iptables', '-t', 'filter', '-F'])
            subprocess.check_call(['iptables', '-t', 'nat', '-F'])
            subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'])
            subprocess.check_call(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'])
            subprocess.check_call(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'INVALID', '-j', 'DROP'])
            subprocess.check_call(['iptables', '-P', 'INPUT', 'DROP'])
            subprocess.check_call(['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'])
            subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'])
            subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'INVALID', '-j', 'DROP'])
            subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'owner', '--uid-owner', 'root', '-j', 'ACCEPT'])
            subprocess.check_call(['iptables', '-P', 'OUTPUT', 'DROP'])
            subprocess.check_call(['iptables', '-P', 'FORWARD', 'DROP'])
            subprocess.check_call(['iptables', '-t', 'nat', '-P', 'PREROUTING', 'ACCEPT'])
            subprocess.check_call(['iptables', '-t', 'nat', '-P', 'POSTROUTING', 'ACCEPT'])
            subprocess.check_call(['iptables', '-t', 'nat', '-P', 'OUTPUT', 'ACCEPT'])

            pipe.close()

            runargs = [ 'runner', '--root', self.root, '--pivot', '--work-dir', '/', '--env=simple', '--ns-ipc', '--ns-uts', '--ns-pid', '--ns-mount', '--mount-proc', '--cap', 'safe' ]
            runargs += [ '--control-host', self.host_ip, '--control-port', str(self.control_port), '--cgroup',  '/', '--cgroup-memory', str(self.cgroup_memory), '--max-realtime', str(self.real_time) ]
            if self.search:
                runargs += [ '--search' ]
            if self.debug:
                runargs += [ '--debug', self.debug ]
            runargs += self.runner_args
            runargs += self.args
            os.execvp('runner', runargs)
        except:
            raise
        finally:
            pipe.close()

    def parent(self):
        subprocess.call(['ip', 'link', 'del', self.host_eth])
        subprocess.check_call(['ip', 'link', 'add', 'name', self.host_eth, 'type', 'veth', 'peer', 'name', self.guest_eth])
        subprocess.check_call(['mount', '--make-rshared', self.root])
        manager = Manager()
        result = manager.dict()
        pipe, pipec = Pipe()
        try:
            child = Process(target = self.child, args=(pipec,))
            child.start()
#WAIT FOR CHILD START AND UNSHARE
            pipe.recv()
            subprocess.check_call(['ifconfig', self.host_eth, self.host_ip, 'netmask', self.netmask, 'up'])
            subprocess.check_call(['ip', 'link', 'set', self.guest_eth, 'netns', str(child.pid)])
            controller = Process(target = self.run_server, args=(self.host_ip, self.control_port, pipe, result, True))
            controller.start()
        except:
            raise
        finally:
            pipe.close()
        child.join()
        self.exitcode = child.exitcode
        controller.terminate()
        self.result = dict(result)

    def run(self):
        self.parent()
        if 'status' not in self.result:
            self.result['status'] = {'is_blob':False, 'value':'INT'}
            self.result['description'] = {'is_blob':False, 'value':'No status in result'}
        return self.result


    def create_handler(self, quiet, result):
        qquiet = quiet
        rresult = result

        class JailHandler(BaseHTTPServer.BaseHTTPRequestHandler):
            quiet = qquiet
            result = rresult
            jail_run = self

            def do_POST(self):
                stime = datetime.datetime.now()
                s = self.rfile.read(int(self.headers['Content-Length']))
                input = yaml.load(s)
                cmd = 'cmd_' + self.path[1:]
                raw_output = {}
                try:
                    raw_output = getattr(self, cmd)(input)
                    output = yaml.dump(raw_output)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/yaml; charset=utf-8")
                    self.send_header("Content-Length", len(output))
                    self.end_headers()
                    self.wfile.write(output)
                except Exception as ex:
                    traceback.print_exc()
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(str(ex))
                etime = datetime.datetime.now()
                if cmd != 'cmd_QUERYCG':
                    print 'served ', cmd, input, raw_output, stime, etime, etime - stime

            @staticmethod
            def oa_for_judge(attr):
                ret = {}
                ret['is_blob'] = bool(attr.is_blob)
                ret['value'] = unicode(attr.value)
                ret['filename'] = unicode(attr.filename)
                return ret

            def cmd_GETSUBMIT(self, input):
                output = {}
                for attr in self.jail_run.submit['submit_data'].get_list():
                    output[unicode(attr.name)] = self.oa_for_judge(attr)
                return output
            
            def cmd_GETTEST(self, input):
                output = {}
                for attr in self.jail_run.submit['test_data'].get_list():
                    output[unicode(attr.name)] = self.oa_for_judge(attr)
                return output
            
            def cmd_GETTESTBLOB(self, input):
                name = input['name']
                fname = jailPath(self.jail_run.root, input['path'])
                self.jail_run.submit['test_data'].get_blob_path(name, fname)
                return { 'res' : 'OK' }
            
            def cmd_GETSUBMITBLOB(self, input):
                name = input['name']
                fname = jailPath(self.jail_run.root, input['path'])
                self.jail_run.submit['submit_data'].get_blob_path(name, fname)
                return { 'res' : 'OK' }
            
            def cgroup_path(self, cg, path):
                root = os.path.join(self.jail_run.cgroup_path, cg, self.jail_run.cgroup)
                if path:
                    root = jailPath(root, path)
                return root
            
            def cmd_CREATECG(self, input):
                for cg in [ 'memory', 'cpuacct', 'cpuset', ] :
                    path = self.cgroup_path(cg, input['group'])
                    if not os.path.isdir(path):
                        os.mkdir(path)
                path = self.cgroup_path('cpuset', input['group'])
                par = os.path.join(path, '..')
                for limit in [ 'cpuset.cpus', 'cpuset.mems', ]:
                    with open(os.path.join(par, limit), 'r') as s:
                        with open(os.path.join(path, limit), 'w') as d:
                            for l in s:
                                d.write(l)
                return { 'res' : 'OK' }

            def cmd_LIMITCG(self, input):
                def set_limit(cg, lim, value):
                    path = self.cgroup_path(cg, input['group'])
                    file = os.path.join(path, lim)
                    with open(file, 'w') as f:
                        f.write(str(value))
                if 'memory' in input:
                    set_limit('memory', 'memory.limit_in_bytes', int(input['memory']))
                return { 'res' : 'OK' }

            def fuser(self, name):
                #return int((subprocess.Popen(["fuser", file], stdout=subprocess.PIPE).communicate()[0]).split(':')[-1])
                name = os.path.basename(name)
                for pid in os.listdir("/proc"):
                    try:
                        for fd in os.listdir(os.path.join("/proc", pid, "fd")):
                            path = os.path.basename(os.path.realpath(os.path.join("/proc", pid, "fd", fd)))
                            if path == name:
                                return pid
                    except:
                        pass
                return None

            def cmd_ASSIGNCG(self, input):
                file = jailPath(self.jail_run.root, input['file'])
                pid = self.fuser(file)
                #TODO: Check pid
                if pid is not None:
                    for cg in [ 'memory', 'cpuacct', 'cpuset', ] :
                        path = self.cgroup_path(cg, input['group'])
                        with open(os.path.join(path, 'tasks'), 'w') as f:
                            f.write(str(pid))
                    return { 'res' : 'OK' }
                return { 'res' : 'FAIL' }
            
            def rec_destroy_cg(self, path):
                for sub in os.listdir(path):
                	sub = os.path.join(path, sub)
                    if os.path.isdir(sub):
                    	self.rec_destroy_cg(sub)
                killer = True
                #TODO: po ilu probach sie poddac?
                while killer:
                    killer = False
                    with open(os.path.join(path, 'tasks'), 'r') as f:
                        for pid in f:
                            killer = True
                            try:
                                os.kill(int(pid), signal.SIGKILL)
                            except OSError:
                                pass
                    time.sleep(1)
                os.rmdir(path)

            def cmd_DESTROYCG(self, input):
                for cg in [ 'memory', 'cpuacct', 'cpuset', ] :
                    path = self.cgroup_path(cg, input['group'])
                    self.rec_destroy_cg(path)
                return { 'res' : 'OK' }

            def cmd_QUERYCG(self, input):
                acct_path = self.cgroup_path('cpuacct', input['group'])
                mem_path = self.cgroup_path('memory', input['group'])
                output = {}
                with open(os.path.join(acct_path, 'cpuacct.usage'), 'r') as f:
                    output['cpu'] = f.readline().strip()
                with open(os.path.join(acct_path, 'cpuacct.stat'), 'r') as f:
                    _, output['cpu.user'] = f.readline().split()
                    _, output['cpu.system'] = f.readline().split()
                with open(os.path.join(mem_path, 'memory.max_usage_in_bytes'), 'r') as f:
                    output['memory'] = f.readline()
                output['res'] = 'OK'
                return output

            def cmd_CREATEJAIL(self, input):
                path = os.path.join(jailPath(self.jail_run.root, input['path']))
                template = input['template']
                jb = JailBuilder(root=path, template_path=self.jail_run.template_path, template=template)
                jb.create()
                try:
                    subprocess.check_call(['mount', '-o', 'rbind', jb.jail_path, path])
                except:
                    jb.destroy()
                    raise
                return { 'res' : 'OK' }

            def cmd_SETSTRING(self, input):
                self.result[input['name']] = {'is_blob': False, 'value': input['value']}
                return { 'res' : 'OK' }

            def cmd_SETBLOB(self, input):
                path = os.path.join(jailPath(self.jail_run.root, input['path']))
                hash = Blob.create_path(path)
                filename = input.get('filename', os.path.basename(path)) 
                self.result[input['name']] = {'is_blob': True, 'value': hash, 'filename': filename}
                return { 'res' : 'OK' }

            def cmd_PING(self, input):
                return { 'res' : 'OK' }

            def log_message(self, *args, **kwargs):
                if not self.quiet:
                    BaseHTTPServer.BaseHTTPRequestHandler.log_message(self, *args, **kwargs)
            def log_request(self, *args, **kwargs):
                if not self.quiet:
                    BaseHTTPServer.BaseHTTPRequestHandler.log_request(self, *args, **kwargs)

        return JailHandler

    def run_server(self, host, port, pipe, result, quiet=False):
        server_class = BaseHTTPServer.HTTPServer
        handler_class = self.create_handler(quiet, result)
        httpd = server_class((host, port), handler_class)
        pipe.send(1)
        try:
            httpd.serve_forever()
        except:
            traceback.print_exc()
        finally:
            httpd.server_close()
