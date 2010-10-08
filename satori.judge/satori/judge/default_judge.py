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
import traceback

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
options.debug = True

#@<checker name="Default judge">
#@      <input>
#@              <value name="time" description="Time limit" required="true"/>
#@              <value name="memory" description="Memory limit (kbytes)" required="true" default="8192"/>
#@              <file name="input" description="Input file" required="true"/>
#@              <file name="hint" description="Output/hint file" required="false"/>
#@              <file name="checker" description="Specific checker" required="false"/>
#@      </input>
#@</checker>


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
language   = ""
compile    = []
time_limit   = int(test.get('time', {'value' : options.execute_time})['value'])
memory_limit = int(test.get('memory', {'value' : options.execute_memory})['value'])
checker      = 'checker' in test and test['checker']['is_blob']

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
if options.debug:
    compile_run += [ '--debug', '/compile.debug.log' ]
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
if options.debug:
    execute_run += [ '--debug', '/execute.debug.log' ]
execute_run += [options.directory+"/solution.x"]
res = subprocess.Popen(execute_run, stdout = subprocess.PIPE).communicate()[0];
ret = res.split()[0]
communicate('SETSTRING', {'name': 'execute.log', 'value': res})


if ret != "OK":
    communicate('SETSTRING', {'name': 'status', 'value': ret})
    sys.exit(0)


communicate('GETTESTBLOB', {'name': 'hint', 'path': '/tmp/data.hint'})
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
    if options.debug:
        check_run += [ '--debug', '/check.debug.log' ]
    check_run += ["/tmp/checker.x", "/tmp/data.in", "/tmp/data.hint", "/tmp/data.out"]
    ret = subprocess.call(check_run)
else:
    ret = subprocess.call(["diff", "-q", "-w", "/tmp/data.hint", "/tmp/data.out"])
if ret != 0:
    communicate('SETSTRING', {'name': 'status', 'value': 'ANS'})
    sys.exit(0)

communicate('SETSTRING', {'name': 'status', 'value': 'OK'})
#print ' '.join(compile_run)
#print ' '.join(execute_run)
#subprocess.call(['bash'])
