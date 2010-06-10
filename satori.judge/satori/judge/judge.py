# vim:ts=4:sts=4:sw=4:expandtab
"""Satori judge implementation.
"""

from satori.objects import Object, Argument
import BaseHTTPServer
import cgi
import os
import signal
import subprocess
import time
import yaml

def checkSubPath(root, path):
    root = os.path.realpath(root).split('/')
    path = os.path.realpath(path).split('/')

    if len(path) < len(root):
    	return False
    for i in range(0, len(root)):
        if root[i] != path[i]:
        	return False
    return True

class JailBuilder(Object):
    safePath = '/cdrom'
    safeExtension = '.template'

    @Argument('root', type=str, default='/jail')
    @Argument('template', type=str, default='/cdrom/jail.template')

    def __init__(self, root, template):
        if not checkSubPath(self.safePath, template) or os.path.splitext(template)[1] != self.safeExtension:
        	raise Exception('Template '+template+' is not safe')
        self.root = root
        self.template = template

    def create(self):
        try:
            os.mkdir(self.root)
            template = yaml.load(open(self.template, 'r'))
            dirlist = []
            quota = 0
            num = 1
            if 'base' in template:
                for base in template['base']:
                	opts = template.get('opts', '')
                	name = template.get('name', '__' + str(num) + '__')
                	num += 1
                    path = os.path.join(self.root, os.path.basename(name))
                    if 'path' in base:
                        type = base.get('type')
                        src = os.path.realpath(base['path'])
                        if os.path.isdir(src):
                            os.mkdir(path)
                            subprocess.check_call(['mount', '-o', 'bind,ro,'+opts, src, path])
                            dirlist.append(path + '=nfsro')
                        elif os.path.isfile(src):
                            os.mkdir(path)
                            if type is None:
                            	ext = os.path.splitext(src)[1]
                                if ext:
                                    type = ext[1:]
                                else:
                                	type = 'auto'
                            subprocess.check_call(['mount', '-t', type, '-o', 'loop,noatime,ro,'+opts, src, path])
                            dirlist.append(path + '=nfsro')
            if 'quota' in template:
                quota = int(template['quota'])
            if quota > 0:
                path = os.path.join(self.root, '__rw__')
                os.mkdir(path)
                subprocess.check_call(['mount', '-t', 'tmpfs', '-o', 'noatime,rw,size=' + str(quota) + 'm', 'tmpfs', path])
                dirlist.append(path + '=rw')
            subprocess.check_call(['mount', '-t', 'aufs', '-o', 'noatime,rw,dirs=' + ':'.join(dirlist), 'aufs', self.root])
            if 'inject' in template: 
                pass #TODO
            if 'remove' in template:
                for path in template['remove']:
                	subprocess.check_call(['rm', '-rf', os.path.join(self.root, os.path.abspath(path))])
            if 'bind' in template:
            	pass #TODO
            if 'proc' in template:
                subprocess.check_call(['mount', '-o', 'bind', '/proc', os.path.join(self.root, 'proc')])
            if 'script' in template:
            	pass #TODO
            subprocess.check_call(['mount', '--rshared', self.root])
            subprocess.check_call(['mount', '--rslave', self.root])
        except:
            self.destroy()
            raise

    def destroy(self):
        while True:
            paths = []
            with open('/proc/mounts', 'r') as mounts:
                for mount in mounts:
                    path = mount.split(' ')[1]
                    if checkSubPath(self.root, path):
                        paths.append(path)
            if len(paths) == 0:
            	break
            paths.reverse()
            for path in paths:
                print 'umount', '-l', path
                subprocess.call(['umount', '-l', path])
        subprocess.check_call(['rm', '-rf', self.root])



class JailHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):
        s = self.rfile.read(int(self.headers['Content-Length']))
        input = yaml.load(s)
        cmd = 'cmd_' + self.path[1:]
        try:
            output = getattr(self, cmd)(input)
            self.send_response(200)
            self.send_header("Content-type", "text/yaml; charset=utf-8")
            self.end_headers()
            yaml.dump(output, self.wfile)
        except Exception as ex:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(ex))
    def cmd_GETSUBMIT(self, input):
        #TODO: Thrift get data
        output = {}
        output['id'] = self.submit_id
        return output
    def cmd_GETTEST(self, input):
        #TODO: Thrift get data
        output = {}
        output['id'] = self.test_id
        return output
    def cmd_GETCACHE(self, input):
        hash = gen_hash(input['what'])
        fname = os.path.join(self.root_path, input['where'])
        #TODO: Przeszukac cache
        return 'OK'
    def cmd_PUTCACHE(self, input):
        hash = gen_hash(input['what'])
        fname = os.path.join(self.root_path, input['where'])
        type = input['how']
        #TODO: Handle cache
        return 'OK'
    def cmd_GETBLOB(self, input):
        hash = input['hash']
        fname = os.path.join(self.root_path, input['where'])
        #TODO: Thrift get blob
        return 'OK'
    def cmd_CREATECG(self, input):
        path = os.path.join(self.cg_root, os.path.abspath(input['path']))
        os.mkdir(path)
        return 'OK'
    def cmd_LIMITCG(self, input):
        path = os.path.join(self.cg_root, os.path.abspath(input['path']))
        def set_limit(type, value):
            file = os.path.join(path, type)
            with open(file, 'w') as f:
                f.write(str(value))
        if 'memory' in input:
        	set_limit('memory.limit_in_bytes', int(input['memory']))
        return 'OK'
    def cmd_ASSIGNCG(self, input):
        path = os.path.join(self.cg_root, os.path.abspath(input['path']))
        pid = int(input['pid'])
        #TODO: Check pid
        with open(os.path.join(path, 'tasks'), 'w') as f:
            f.write(str(pid))
        return 'OK'
    def cmd_DESTROYCG(self, input):
        path = os.path.join(self.cg_root, os.path.abspath(input['path']))
        killer = True
        #TODO: po ilu probach sie poddac?
        while killer:
        	killer = False
            with open(os.path.join(path, 'tasks'), 'r') as f:
                for pid in f:
                	killer = True
                	os.kill(int(pid), signal.SIGKILL)
            time.sleep(1)
        return 'OK'
    def cmd_QUERYCG(self, input):
        path = os.path.join(self.cg_root, os.path.abspath(input['path']))
        output = {}
        with open(os.path.join(path, 'cpuacct.stat'), 'r') as f:
            _, output['cpu.user'] = f.readline().split()
            _, output['cpu.system'] = f.readline().split()
        with open(os.path.join(path, 'memory.max_usage_in_bytes'), 'r') as f:
            output['memory'] = f.readline()
        return output







def create_handler(submit, test, root, cgroot):
    class Handler(JailHandler):
        def __init__(self, *args, **kwargs):
            self.submit_id = submit
            self.test_id = test
            self.root_path = root
            self.cg_root = cgroot
            JailHandler.__init__(self, *args, **kwargs)
    return Handler


def run_server(host, port):
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((host, port), create_handler(1, 2, '/jail', '/root/cg/satori.judge'))
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


#run_server('127.0.0.1', 8765)
jb = JailBuilder(root='/dev')
jb.destroy()

