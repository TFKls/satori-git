#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

#@<checker name="Default judge">
#@    <input>
#@        <value name="time" description="Time limit (miliseconds)" required="true"/>
#@        <value name="memory" description="Memory limit (bytes)" required="true" default="268435456"/>
#@        <file name="input" description="Input file" required="true"/>
#@        <file name="hint" description="Output/hint file" required="false"/>
#@        <file name="checker" description="Specific checker" required="false"/>
#@    </input>
#@</checker>

import datetime
import getpass
import httplib
import logging
import os
import shutil
import subprocess
import sys
import time
import yaml
import traceback
from optparse import OptionParser

parser = OptionParser()

parser.add_option('-d', '--debug', dest='debug', action='store_true', default=False)

parser.add_option('-H', '--control-host', dest='host', default='192.168.100.101', action='store', type='string')
parser.add_option('-P', '--control-port', dest='port', default=8765, action='store', type='int')

parser.add_option('-J', '--jail', dest='jail', default='/jail', action='store', type='string')
parser.add_option('-T', '--template', dest='template', default='judge', action='store', type='string')
parser.add_option('-U', '--user', dest='user', default='runner', action='store', type='string')
parser.add_option('-G', '--group', dest='group', default='runner', action='store', type='string')
parser.add_option('-D', '--directory', dest='directory', default='/runner', action='store', type='string')

parser.add_option('--default-compile-time', dest='compile_time', default=20*1000, action='store', type='int')
parser.add_option('--default-compile-memory', dest='compile_memory', default=256*1024*1024, action='store', type='int')
parser.add_option('--default-execute-time', dest='execute_time', default=10*1000, action='store', type='int')
parser.add_option('--default-execute-memory', dest='execute_memory', default=256*1024*1024, action='store', type='int')
parser.add_option('--default-checker-time', dest='checker_time', default=60*1000, action='store', type='int')
parser.add_option('--default-checker-memory', dest='checker_memory', default=1024*1024*1024, action='store', type='int')

(options, args) = parser.parse_args()

def parse_time(timestr):
    return 0
def parse_memory(memorystr):
    return 0

options.jail = os.path.abspath(os.path.join('/', options.jail))
options.directory = os.path.abspath(os.path.join('/', options.directory))[1:]

def communicate(cmd, args={}, check=True):
    yam = yaml.dump(args)
    try:
        con = httplib.HTTPConnection(options.host, options.port)
        con.request('POST', '/' + cmd, yam)
        res = con.getresponse()
        ret = yaml.load(res.read())
    except:
        traceback.print_exc()
        raise Exception('Communication '+cmd+' failed')
    if check and ('res' not in ret or ret['res'] != 'OK'):
        raise Exception('Communication '+cmd+' finished with failure')
    return ret


submit = communicate('GETSUBMIT', check=False)
test   = communicate('GETTEST', check=False)

filename   = submit['content']['filename']
fileext    = filename.split(".")[-1].lower()
time_limit   = int(test.get('time', {'value' : options.execute_time})['value'])
memory_limit = int(test.get('memory', {'value' : options.execute_memory})['value'])
has_checker  = 'checker' in test and test['checker']['is_blob']

if fileext == 'c':
    source_file = "solution.c"
    exec_file   = "solution.x"
    compiler  = [ '/usr/bin/gcc', '-static', '-O2', '-Wall', 'solution.c', '-lm', '-osolution.x', '-include', 'stdio.h', '-include', 'stdlib.h', '-include', 'string.h']
elif fileext in ["cpp", "cc", "cxx"]:
    source_file = "solution.cpp"
    exec_file   = "solution.x"
    compiler  = [ '/usr/bin/g++', '-static', '-O2', '-Wall', 'solution.cpp', '-osolution.x', '-include', 'cstdio', '-include', 'cstdlib', '-include', 'cstring']
elif fileext in ["pas", "p", "pp"]:
    source_file = "solution.pas"
    exec_file   = "solution.x"
    compiler  = [ '/usr/bin/fpc', '-Sgic', '-Xs', '-viwnh', '-OG2', '-Wall', 'solution.pas', '-osolution.x']
else:
    communicate('SETSTRING', {'name': 'status', 'value': 'EXT'})
    sys.exit(0)

communicate('CREATEJAIL', {'path': options.jail, 'template': options.template})

communicate('GETSUBMITBLOB', {'name': 'content', 'path': os.path.join(options.jail, options.directory, source_file)})
#COMPILE
compile_run = ["runner", "--quiet",
      "--root="+options.jail,
      "--work-dir="+options.directory,
      "--env=simple",
      "--setuid="+options.user,
      "--setgid="+options.group,
      "--control-host="+options.host,
      "--control-port="+str(options.port),
      "--cgroup=/compile",
      "--cgroup-memory="+str(options.compile_memory),
      "--cgroup-cputime="+str(options.compile_time),
      "--max-memory="+str(options.compile_memory),
      "--max-cputime="+str(options.compile_time),
      "--max-realtime="+str(options.compile_time),
      "--stdout=/compile.log", "--trunc-stdout",
      "--stderr=__STDOUT__",
      "--priority=30"]
if options.debug:
    compile_run += [ '--debug', '/compile.debug.log' ]
compile_run += compiler
ret = subprocess.call(compile_run)
communicate('SETBLOB', {'name': 'compile.log', 'path': '/compile.log'})
if options.debug:
    communicate('SETBLOB', {'name': 'compile.debug.log', 'path': '/compile.debug.log'})
if ret:
    communicate('SETSTRING', {'name': 'status', 'value': 'CME'})
    sys.exit(0)


communicate('GETTESTBLOB', {'name': 'input', 'path': '/tmp/data.in'})
#RUN
execute_run = ["runner",
      "--root="+options.jail,
      "--work-dir="+options.directory,
      "--env=empty",
      "--setuid="+options.user,
      "--setgid="+options.group,
      "--control-host="+options.host,
      "--control-port="+str(options.port),
      "--cgroup=/execute",
      "--cgroup-memory="+str(memory_limit),
      "--cgroup-cputime="+str(time_limit),
      "--max-memory="+str(memory_limit),
      "--max-cputime="+str(time_limit),
      "--max-realtime="+str(int(1.5*time_limit)),
      "--max-threads=1",
      "--max-files=4",
      "--stdin=/tmp/data.in",
      "--stdout=/tmp/data.out", "--trunc-stdout",
      "--stderr=/dev/null",
      "--memlock",
      "--priority=30"]
if options.debug:
    execute_run += [ '--debug', '/execute.debug.log' ]
execute_run += [ os.path.join('/', options.directory, exec_file) ]
res = subprocess.Popen(execute_run, stdout = subprocess.PIPE).communicate()[0];
ret = res.split()[0]
communicate('SETSTRING', {'name': 'execute.log', 'value': res})
if options.debug:
    communicate('SETBLOB', {'name': 'execute.debug.log', 'path': '/execute.debug.log'})
if ret != "OK":
    communicate('SETSTRING', {'name': 'status', 'value': ret})
    sys.exit(0)


communicate('GETTESTBLOB', {'name': 'hint', 'path': '/tmp/data.hint'})
#TEST
if has_checker:
    communicate('GETTESTBLOB', {'name': 'checker', 'path': '/tmp/checker.x'})
    os.chmod("/tmp/checker.x",0755)
    checker = ["/tmp/checker.x", "/tmp/data.in", "/tmp/data.hint", "/tmp/data.out"]
else:
	checker = ["/usr/bin/diff", "-q", "-w", "/tmp/data.hint", "/tmp/data.out"]

check_run = ["runner",
      "--quiet",
      "--root=/",
      "--work-dir=/tmp",
      "--env=simple",
      "--setuid="+options.user,
      "--setgid="+options.group,
      "--control-host="+options.host,
      "--control-port="+str(options.port),
      "--cgroup=/check",
      "--cgroup-memory="+str(options.checker_memory),
      "--cgroup-cputime="+str(options.checker_time),
      "--max-memory="+str(options.checker_memory),
      "--max-cputime="+str(options.checker_time),
      "--max-realtime="+str(options.checker_time),
      "--max-threads=1",
      "--max-files=7",
      "--stdout=/check.log", "--trunc-stdout",
      "--stderr=__STDOUT__",
      "--priority=30"]
if options.debug:
    check_run += [ '--debug', '/check.debug.log' ]
check_run += checker
ret = subprocess.call(check_run)
communicate('SETBLOB', {'name': 'check.log', 'path': '/check.log'})
if options.debug:
    communicate('SETBLOB', {'name': 'check.debug.log', 'path': '/check.debug.log'})
if ret != 0:
    communicate('SETSTRING', {'name': 'status', 'value': 'ANS'})
    sys.exit(0)

communicate('SETSTRING', {'name': 'status', 'value': 'OK'})
