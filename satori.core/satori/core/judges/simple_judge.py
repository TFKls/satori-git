#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

#@<checker name="Simple judge">
#@      <input>
#@              <param type="time" name="time" description="Time limit" required="true" default="10s"/>
#@              <param type="size" name="memory" description="Memory limit" required="true" default="256MB"/>
#@              <param type="blob" name="input" description="Input file" required="true"/>
#@              <param type="blob" name="hint" description="Output/hint file" required="false"/>
#@              <param type="blob" name="checker" description="Checker" required="false"/>
#@              <param type="text" name="languages" description="Accepted languages" required="false" default="c,cpp,pas"/>
#@      </input>
#@      <output>
#@              <param type="text" name="status" description="Status"/>
#@              <param type="blob" name="compile_log" description="Compilation log"/>
#@              <param type="time" name="execute_time_real" description="Execution time"/>
#@              <param type="time" name="execute_time_cpu" description="Execution CPU time"/>
#@              <param type="size" name="execute_memory" description="Execution memory"/>
#@              <param type="blob" name="check_log" description="Checking log"/>
#@      </output>
#@</checker>

import httplib
import math
import os
import subprocess
import sys
import yaml
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
        mul = 0.000000001
        timestr = timestr[:-1]
    return int(math.ceil(float(timestr) * mul * 1000))

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

parser = OptionParser()
parser.add_option('-H', '--control-host', dest='host', default='192.168.100.101', action='store', type='string')
parser.add_option('-P', '--control-port', dest='port', default=8765, action='store', type='int')
(options, args) = parser.parse_args()

compile_time = 20*1000
compile_memory = 1024*1024*1024
compile_stack = 64*1024*1024
check_time = 60*1000
check_memory = 1024*1024*1024

def communicate(cmd, args={}, check=True):
    yam = yaml.dump(args)
    try:
        con = httplib.HTTPConnection(options.host, options.port)
        con.request('POST', '/' + cmd, yam)
        res = con.getresponse()
        ret = yaml.load(res.read())
    except:
        raise Exception('Communication '+cmd+' failed')
    if check and ('res' not in ret or ret['res'] != 'OK'):
        raise Exception('Communication '+cmd+' finished with failure')
    return ret

submit = communicate('GETSUBMIT', check=False)
test   = communicate('GETTEST', check=False)

filename     = submit['content']['filename']
fileext      = filename.split('.')[-1].lower()
time_limit   = parse_time(test.get('time')['value'])
memory_limit = parse_memory(test.get('memory')['value'])

if fileext == 'c':
    source_file = 'solution.c'
    compiler  = [ '/usr/bin/gcc', '-static', '-O2', '-Wall', 'solution.c', '-lm', '-osolution.x']
elif fileext in ['cpp', 'cc', 'cxx']:
    fileext = 'cpp'
    source_file = 'solution.cpp'
    compiler  = [ '/usr/bin/g++', '-static', '-O2', '-Wall', 'solution.cpp', '-osolution.x']
elif fileext in ['pas', 'p', 'pp']:
    fileext = 'pas'
    source_file = 'solution.pas'
    compiler  = [ '/usr/bin/fpc', '-Sgic', '-Xs', '-viwnh', '-OG2', '-Wall', 'solution.pas', '-osolution.x']
else:
    communicate('SETSTRING', {'name': 'status', 'value': 'EXT'})
    sys.exit(0)

communicate('CREATEJAIL', {'path': '/jail', 'template': 'judge'})

#COMPILE SOLUTION
communicate('GETSUBMITBLOB', {'name': 'content', 'path': os.path.join('/jail/runner', source_file)})
compile_run = ['runner', '--quiet',
      '--root=/jail',
      '--work-dir=/runner',
      '--env=simple',
      '--setuid=runner',
      '--setgid=runner',
      '--control-host='+options.host,
      '--control-port='+str(options.port),
      '--cgroup=/compile',
      '--cgroup-memory='+str(compile_memory),
      '--cgroup-cputime='+str(compile_time),
      '--max-realtime='+str(compile_time),
      '--max-stack='+str(compile_stack),
      '--stdout=/tmp/compile.log', '--trunc-stdout',
      '--stderr=__STDOUT__',
      '--priority=30']
compile_run += compiler
ret = subprocess.call(compile_run)
communicate('SETBLOB', {'name': 'compile_log', 'path': '/tmp/compile.log'})
if ret != 0:
    communicate('SETSTRING', {'name': 'status', 'value': 'CME'})
    sys.exit(0)

#RUN SOLUTION
communicate('GETTESTBLOB', {'name': 'input', 'path': '/tmp/data.in'})
execute_run = ['runner',
      '--root=/jail',
      '--work-dir=/runner',
      '--env=empty',
      '--setuid=runner',
      '--setgid=runner',
      '--control-host='+options.host,
      '--control-port='+str(options.port),
      '--cgroup=/execute',
      '--max-memory='+str(memory_limit),
      '--max-cputime='+str(time_limit),
      '--max-realtime='+str(int(1.5*time_limit)),
      '--max-threads=1',
      '--max-files=4',
      '--stdin=/tmp/data.in',
      '--stdout=/tmp/data.out', '--trunc-stdout',
      '--stderr=/dev/null',
      '--priority=30']
execute_run += ['/runner/solution.x']
res = subprocess.Popen(execute_run, stdout = subprocess.PIPE).communicate()[0]
ret = res.splitlines()[0]
stats = {}
for line in res.splitlines()[1:]:
    key = line.split(':')[0].strip().lower()
    value = u':'.join(line.split(':')[1:]).strip()
    stats[key] = value
communicate('SETSTRING', {'name': 'execute_time_real', 'value': str(float(stats['time'])/1000)+'s'})
communicate('SETSTRING', {'name': 'execute_time_cpu', 'value': str(float(stats['cpu'])/1000)+'s'})
communicate('SETSTRING', {'name': 'execute_memory', 'value': str(int(stats['memory']))+'B'})
if ret != 'OK':
    communicate('SETSTRING', {'name': 'status', 'value': ret})
    sys.exit(0)

has_checker = 'checker' in test

#COMPILE CHECKER
if has_checker:
    communicate('GETTESTBLOB', {'name': 'checker', 'path': '/tmp/checker.cpp'})
    checker_compiler  = [ '/usr/bin/g++', '-static', '-O2', 'checker.cpp', '-ochecker.x']
    checker_compile_run = ['runner', '--quiet',
          '--root=/',
          '--work-dir=/tmp',
          '--env=simple',
          '--setuid=runner',
          '--setgid=runner',
          '--control-host='+options.host,
          '--control-port='+str(options.port),
          '--cgroup=/compile_checker',
          '--cgroup-memory='+str(compile_memory),
          '--cgroup-cputime='+str(compile_time),
          '--max-realtime='+str(compile_time),
          '--max-stack='+str(compile_stack),
          '--stdout=/tmp/check.log', '--trunc-stdout',
          '--stderr=__STDOUT__',
          '--stdout=/dev/null',
          '--stderr=/dev/null',
          '--priority=30']
    checker_compile_run += checker_compiler
    ret = subprocess.call(checker_compile_run)
    if ret != 0:
        communicate('SETBLOB', {'name': 'check_log', 'path': '/tmp/check.log'})
        communicate('SETSTRING', {'name': 'status', 'value': 'INT'})
        sys.exit(0)

#CHECK OUTPUT
has_hint = 'hint' in test
if has_hint:
    communicate('GETTESTBLOB', {'name': 'hint', 'path': '/tmp/data.hint'})
    hint_file = '/tmp/data.hint'
else:
    hint_file = '/dev/null'
if has_checker:
    checker = ['/tmp/checker.x', '/tmp/data.in', hint_file, '/tmp/data.out']
else:
    checker = ['/usr/bin/diff', '-q', '-w', '-B', hint_file, '/tmp/data.out']
checker_run = ['runner', '--quiet',
      '--root=/',
      '--work-dir=/tmp',
      '--env=simple',
      '--setuid=runner',
      '--setgid=runner',
      '--control-host='+options.host,
      '--control-port='+str(options.port),
      '--cgroup=/check',
      '--cgroup-memory='+str(check_memory),
      '--cgroup-cputime='+str(check_time),
      '--max-realtime='+str(check_time),
      '--stdout=/tmp/check.log',
      '--stderr=__STDOUT__',
      '--priority=30']
if not has_checker:
    checker_run += ['--trunc-stdout']
checker_run += checker
ret = subprocess.call(checker_run)
communicate('SETBLOB', {'name': 'check_log', 'path': '/tmp/check.log'})
if ret != 0:
    communicate('SETSTRING', {'name': 'status', 'value': 'ANS'})
    sys.exit(0)

has_languages = 'languages' in test
if has_languages:
        languages = [ l.strip().lower() for l in test.get('languages')['value'].split(',') ]
    if fileext not in languages:
        communicate('SETSTRING', {'name': 'status', 'value': 'LANG'})

communicate('SETSTRING', {'name': 'status', 'value': 'OK'})
