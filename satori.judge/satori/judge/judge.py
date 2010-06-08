# vim:ts=4:sts=4:sw=4:expandtab
"""Satori judge implementation.
"""

import BaseHTTPServer
import cgi
import yaml
import os
import signal
import time

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
        except Exception ex:
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
        #TODO: Przeszukać cache
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
    httpd = server_class((host, port), create_handler(1,2))
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


run_server('127.0.0.1', 8765)
