#!/usr/bin/env python
# vim:ts=4:sts=4:sw=4:expandtab

import datetime
import getpass
import httplib
import logging
from optparse import OptionParser
import os
import shutil
import subprocess
import sys
import time
import yaml

parser = OptionParser()
parser.add_option('-H', '--control-host', dest='host', default='192.168.100.101', action='store', type='string')
parser.add_option('-P', '--control-port', dest='port', default=8765, action='store', type='int')

(options, args) = parser.parse_args()


options.user = 'runner'
options.group = 'runner'
options.directory = '/runner'
options.compile_time = 60*1000
options.compile_memory = 64*1024*1024
options.execute_time = 10*1000
options.execute_memory = 64*1024*1024
options.check_time = 60*1000
options.check_memory = 64*1024*1024



def communicate(cmd, args={}):
    yam = yaml.dump(args)
    con = httplib.HTTPConnection(options.host, options.port)
    con.request("POST", "/" + cmd, yam, {'Content-Length': len(yam)})
    res = con.getresponse()
    return yaml.load(res.read())



print 'hello'
print communicate('PING', {'hello':'hello'})

submit = communicate('GETSUBMIT')
test   = communicate('GETTEST')

filename   = submit['filename']
fileext    = filename.split(".")[-1].lower()
language   = ""
compile    = []
size_limit   = int(test.get('sizelimit', 100*1024))
time_limit   = int(test.get('time', options.execute_time))
memory_limit = int(test.get('memory', options.execute_memory))
checker      = 'checker' in test

if fileext == 'c':
    language = 'c'
    compile  = [ '/usr/bin/gcc', '-static', '-O2', '-Wall', 'solution.c', '-lm', '-osolution.x', '-include', 'stdio.h', '-include', 'stdlib.h', '-include', 'string.h']
elif fileext in ["cpp", "cc", "cxx"]:
    language = "cpp"
    compile  = [ '/usr/bin/g++', '-static', '-O2', '-Wall', 'solution.cpp', '-osolution.x', '-include', 'cstdio', '-include', 'cstdlib', '-include', 'cstring']
elif fileext in ["pas", "p", "pp"]:
    language = "pas"
    compile  = [ '/usr/bin/fpc', '-Sgic', '-Xs', '-viwnh', '-OG2', '-Wall', 'solution.pas', '-osolution.x']

communicate('CREATEJAIL', {'path': '/jail', 'template': 'judge'})
communicate('GETSUBMITBLOB', {'name': 'content', 'path': '/jail'+options.directory+'/solution.'+language})
#COMPILE
compile_run = ["runner", "--quiet",
      "--root=/jail", "--work-dir="+options.directory, "--env=simple",
      "--setuid="+options.user, "--setgid="+options.group,
      "--control-host="+options.host, "--control-port="+str(options.port),
      "--cgroup=/compile",
      "--cgroup-memory="+str(options.compile_memory),
      "--cgroup-cputime="+str(options.compile_time),
      "--max-memory="+str(options.compile_memory),
      "--max-cputime="+str(options.compile_time),
      "--max-realtime="+str(options.compile_time),
      "--stdout=/compile.log", "--trunc-stdout",
      "--stderr=__STDOUT__",
      "--priority=30"]
compile_run += compile
ret = subprocess.call(compile_run)
if ret:
    communicate('SETSTRING', {'name': 'status', 'value': 'CME'})
    sys.exit(0)
communicate('SETBLOB', {'name': 'compile.log', 'path': '/compile.log'})


communicate('GETTESTBLOB', {'name': 'input', 'path': '/tmp/data.in'})
#RUN
execute_run = ["runner",
      "--root=/jail", "--work-dir="+options.directory, "--env=empty",
      "--setuid="+options.user, "--setgid="+options.group,
      "--control-host="+options.host, "--control-port="+str(options.port),
      "--cgroup=/execute",
      "--cgroup-memory="+str(memory_limit),
      "--cgroup-cputime="+str(time_limit),
      "--max-memory="+str(memory_limit),
      "--max-cputime="+str(time_limit),
      "--max-realtime="+str(int(1.5*time_limit)),
      "--max-threads=1", "--max-files=4",
      "--stdin=/tmp/data.in",
      "--stdout=/tmp/data.out", "--trunc-stdout",
      "--stderr=/dev/null",
      "--memlock",
      "--priority=30"]
execute_run += [options.directory+"/solution.x"]
res = subprocess.Popen(execute_run, stdout = subprocess.PIPE).communicate()[0];
print "RES : "+res
ret = res.split()[0]
print "RET : "+ret
communicate('SETSTRING', {'name': 'execute.log', 'value': res})
if ret != "OK":
    communicate('SETSTRING', {'name': 'status', 'value': ret})
    sys.exit(0)


communicate('GETTESTBLOB', {'name': 'output', 'path': '/tmp/data.hint'})
#TEST
if checker:
    communicate('GETTESTBLOB', {'name': 'checker', 'path': '/tmp/checker.x'})
    os.chmod("/tmp/checker.x",0755)
    check_run = ["runner", "--quiet",
          "--root=/", "--work-dir=/tmp", "--env=simple",
          "--setuid="+options.user, "--setgid="+options.group,
          "--control-host="+options.host, "--control-port="+str(options.port),
          "--cgroup=/check",
          "--cgroup-memory="+str(options.check_memory),
          "--cgroup-cputime="+str(options.check_time),
          "--max-memory="+str(options.check_memory),
          "--max-cputime="+str(options.check_time),
          "--max-realtime="+str(options.check_time),
          "--stdout=/check.log", "--trunc-stdout",
          "--stderr=__STDOUT__",
          "--max-threads=1", "--max-files=7",
          "--priority=30"]
    check_run += ["/tmp/checker.x", "/tmp/data.in", "/tmp/data.hint", "/tmp/data.out"]
    ret = subprocess.call(check_run)
    if ret != 0:
        communicate('SETSTRING', {'name': 'status', 'value': 'ANS'})
        sys.exit(0)
else:
    ret = subprocess.call(["diff", "-q", "-w", "/tmp/data.hint", "/tmp/data.out"])
    if ret != 0:
        communicate('SETSTRING', {'name': 'status', 'value': 'ANS'})
        sys.exit(0)

communicate('SETSTRING', {'name': 'status', 'value': 'OK'})
#print ' '.join(compile_run)
#print ' '.join(execute_run)
#subprocess.call(['bash'])
