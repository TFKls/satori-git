#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

#@<checker name="ACM style judge script">
#@      <input>
#@              <param type="time" name="time" description="Time limit" required="true" default="10s"/>
#@              <param type="size" name="memory" description="Memory limit" required="true" default="256MB"/>
#@              <param type="blob" name="input" description="Input file" required="false"/>
#@              <param type="blob" name="hint" description="Output/hint file" required="false"/>
#@              <param type="blob" name="checker" description="Specific checker" required="false"/>
#@      </input>
#@      <output>
#@              <param type="text" name="status" description="Status" required="true"/>
#@              <param type="blob" name="compile_log" description="Compilation log"/>
#@              <param type="time" name="execute_time_real" description="Execution time"/>
#@              <param type="time" name="execute_time_cpu" description="Execution CPU time"/>
#@              <param type="size" name="execute_memory" description="Execution memory"/>
#@              <param type="blob" name="check_log" description="Checker log" required="false"/>
#@      </output>
#@</checker>

import datetime
import getpass
import httplib
import logging
import math
import os
import shutil
import subprocess
import sys
import time
import yaml
import traceback
from optparse import OptionParser

def parse_time(timestr):
    mul = 0.001
    timestr = unicode(timestr.strip().lower())
    if timestr[-1] == 's':
        mul = 1
        timestr = timestr[:-1]
    if timestr[-1] == 'c':
        mul = 0.01
        timestr = timestr[:-1]
    elif timestr[-1] == 'm':
        mul = 0.001
        timestr = timestr[:-1]
    elif timestr[-1] == u'µ':
        mul = 0.000001
        timestr = timestr[:-1]
    elif timestr[-1] == 'n':
        timestr = mul = 0.000000001
        timestr[0:-1]
    return int(math.ceil(float(timestr) * mul * 1000))
def parse_time_callback(option, opt_str, value, parser):
    setattr(parser.values, option.dest, parse_time(value))

def parse_memory(memstr):
    mul = 1
    memstr = unicode(memstr.strip().lower())
    if memstr[-1] == 'b':
        mul = 1
        memstr = memstr[:-1]
    if memstr[-1] == 'k':
        mul = 1024
        memstr = memstr[:-1]
    elif memstr[-1] == 'm':
        mul = 1024**2
        memstr = memstr[:-1]
    elif memstr[-1] == 'g':
        mul = 1024**3
        memstr = memstr[:-1]
    elif memstr[-1] == 't':
        mul = 1024**4
        memstr = memstr[:-1]
    elif memstr[-1] == 'p':
        mul = 1024**5
        memstr = memstr[:-1]
    return int(math.ceil(float(memstr) * mul))
def parse_memory_callback(option, opt_str, value, parser):
    setattr(parser.values, option.dest, parse_memory(value))

parser = OptionParser()

parser.add_option('-d', '--debug', dest='debug', action='store_true', default=False)

parser.add_option('-H', '--control-host', dest='host', default='192.168.100.101', action='store', type='string')
parser.add_option('-P', '--control-port', dest='port', default=8765, action='store', type='int')

parser.add_option('-J', '--jail', dest='jail', default='/jail', action='store', type='string')
parser.add_option('-T', '--template', dest='template', default='judge', action='store', type='string')
parser.add_option('-U', '--user', dest='user', default='runner', action='store', type='string')
parser.add_option('-G', '--group', dest='group', default='runner', action='store', type='string')
parser.add_option('-D', '--directory', dest='directory', default='/runner', action='store', type='string')

parser.add_option('--default-compile-time', dest='compile_time', default=20*1000, type='int', action="callback", callback=parse_time_callback)
parser.add_option('--default-compile-memory', dest='compile_memory', default=256*1024*1024, type='int', action="callback", callback=parse_memory_callback)
parser.add_option('--default-execute-time', dest='execute_time', default=10*1000, type='int', action="callback", callback=parse_time_callback)
parser.add_option('--default-execute-memory', dest='execute_memory', default=256*1024*1024, type='int', action="callback", callback=parse_memory_callback)
parser.add_option('--default-checker-time', dest='checker_time', default=60*1000, type='int', action="callback", callback=parse_time_callback)
parser.add_option('--default-checker-memory', dest='checker_memory', default=1024*1024*1024, type='int', action="callback", callback=parse_memory_callback)

(options, args) = parser.parse_args()

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
if 'time' in test and not test['time']['is_blob']:
    time_limit = parse_time(test.get('time')['value'])
else:
    time_limit = options.execute_time
if 'memory' in test and not test['memory']['is_blob']:
    memory_limit = parse_memory(test.get('memory')['value'])
else:
    time_limit = options.execute_memory
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


#COMPILE
communicate('GETSUBMITBLOB', {'name': 'content', 'path': os.path.join(options.jail, options.directory, source_file)})
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
compile_run += compiler
ret = subprocess.call(compile_run)
communicate('SETBLOB', {'name': 'compile_log', 'path': '/compile.log'})
if ret:
    communicate('SETSTRING', {'name': 'status', 'value': 'CME'})
    sys.exit(0)


#RUN
communicate('GETTESTBLOB', {'name': 'input', 'path': '/tmp/data.in'})
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
execute_run += [ os.path.join('/', options.directory, exec_file) ]
res = subprocess.Popen(execute_run, stdout = subprocess.PIPE).communicate()[0];
ret = res.splitlines()[0]
stats = {}
for line in res.splitlines()[1:]:
    key = line.split(':')[0].strip().lower()
    value = u':'.join(line.split(':')[1:]).strip()
    stats[key] = value
communicate('SETSTRING', {'name': 'execute_time_real', 'value': str(float(stats['time'])/1000)})
communicate('SETSTRING', {'name': 'execute_time_cpu', 'value': str(float(stats['cpu'])/1000)})
communicate('SETSTRING', {'name': 'execute_memory', 'value': str(int(stats['memory']))})
if ret != "OK":
    communicate('SETSTRING', {'name': 'status', 'value': ret})
    sys.exit(0)

#TEST
communicate('GETTESTBLOB', {'name': 'hint', 'path': '/tmp/data.hint'})
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
check_run += checker
ret = subprocess.call(check_run)
communicate('SETBLOB', {'name': 'check_log', 'path': '/check.log'})
if ret != 0:
    communicate('SETSTRING', {'name': 'status', 'value': 'ANS'})
    sys.exit(0)

communicate('SETSTRING', {'name': 'status', 'value': 'OK'})
