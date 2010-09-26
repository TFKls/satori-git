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
options.compile_time = 60*1000
options.compile_memory = 64*1024*1024



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

result = 'OK'

filename   = submit['filename']
fileext    = filename.split(".")[-1].lower()
language   = ""
compile    = []
sizelimit  = int(test.get('sizelimit', 100*1024))

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
communicate('GETSUBMITBLOB', {'name': 'content', 'path': '/jail/tmp/solution.'+language})
#COMPILE
compile_run = ["runner", "--quiet",
      "--root=/jail", "--work-dir=/tmp", "--env=empty",
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
    result = "CME"


print ' '.join(compile_run)
subprocess.call(['bash'])





communicate('GETTESTBLOB', {'name': 'input', 'path': '/jail/tmp/data.in'})
#RUN


communicate('GETTESTBLOB', {'name': 'output', 'path': '/jail/tmp/data.out'})
#TEST

exefile = ""
logging.info("Compiling HASH "+str(judge.hash)+" JID "+str(judge.submit.id)+" -- Problem: "+judge.problem.id+" -- Timestamp: "+submittime)
logging.info("Filename: "+filename+" from "+judge.user.id+" in "+roomname+" ("+fullname+")")
try:
  subprocess.call(["mkchroot", "-D", "/athina/chroot"], stdout = open("/dev/null", "w"), stderr = subprocess.STDOUT)
  subprocess.check_call(["mkchroot", "--base=full", "--quota=128", "/athina/chroot"], stdout = open("/dev/null", "w"), stderr = subprocess.STDOUT)
  if language == "gnuc":
    judge.submit.getfile("data", "/athina/chroot/tmp/src.c")
    ret = subprocess.call(["runner", "--quiet",
      "--root=/athina/chroot", "--work-dir=/tmp", "--env=full",
      "--setuid="+str(athinauid), "--setgid="+str(athinagid),
      "--max-realtime=60000", "--max-cputime=60000", "--max-memory="+str(64*1024*1024),
      "--stdout=/athina/chroot/compile.log", "--trunc-stdout",
      "--stderr=__STDOUT__",
      "--priority=30",
      "/usr/bin/gcc", "-static", "-O2", "-Wall", "src.c", "-lm", "-obin", "-include", "stdio.h", "-include", "stdlib.h", "-include", "string.h"])
    if ret:
      judge.result = "CME"
  elif language == "cxx":
    judge.submit.getfile("data", "/athina/chroot/tmp/src.cpp")
    ret = subprocess.call(["runner", "--quiet",
      "--root=/athina/chroot", "--work-dir=/tmp", "--env=full",
      "--setuid="+str(athinauid), "--setgid="+str(athinagid),
      "--max-realtime=60000", "--max-cputime=60000", "--max-memory="+str(64*1024*1024),
      "--stdout=/athina/chroot/compile.log", "--trunc-stdout",
      "--stderr=__STDOUT__",
      "--priority=30",
      "/usr/bin/g++", "-static", "-O2", "-Wall", "src.cpp", "-obin", "-include", "cstdio", "-include", "cstdlib", "-include", "cstring"])
    if ret:
      judge.result = "CME"
  elif language == "pascal":
    judge.submit.getfile("data", "/athina/chroot/tmp/src.pas")
    ret = subprocess.call(["runner", "--quiet",
      "--root=/athina/chroot", "--work-dir=/tmp", "--env=full",
      "--setuid="+str(athinauid), "--setgid="+str(athinagid),
      "--max-realtime=60000", "--max-cputime=60000", "--max-memory="+str(64*1024*1024),
      "--stdout=/athina/chroot/compile.log", "--trunc-stdout",
      "--stderr=__STDOUT__",
      "--priority=30",
      "/usr/bin/fpc", "-Sgic", "-Xs", "-viwnh", "-OG2", "-Wall", "src.pas", "-obin"])
    if ret:
      judge.result = "CME"
  with open("/athina/chroot/compile.log") as f:
    judge.log += str(f.read(65536))

  if os.path.exists("/athina/chroot/tmp/bin"):
    with open("/athina/chroot/tmp/bin","r") as f:
      exefile = f.read();
finally:
  subprocess.call(["mkchroot", "-D", "/athina/chroot"], stdout = open("/dev/null", "w"), stderr = subprocess.STDOUT)

if judge.result == "" and exefile == "":
  judge.result = "CME"
  judge.log += "Compilation failed.\n"
elif judge.result == "":
  judge.result = "OK";
  numtests = int(judge.problem.get("testcount"))
  checkfile = judge.problem.get("checker")
  for i in range(0, numtests):
    try:
      judge.settest(i)
      subprocess.call(["mkchroot", "-D", "/athina/chroot"], stdout = open("/dev/null", "w"), stderr = subprocess.STDOUT)
      subprocess.check_call(["mkchroot", "--base=full", "--quota=512", "/athina/chroot"], stdout = open("/dev/null", "w"), stderr = subprocess.STDOUT)
      tle = int(judge.test.get("tle"))
      mem = int(judge.test.get("mem"))
      judge.test.getfile("in", "/athina/chroot/in")
      judge.test.getfile("out", "/athina/chroot/hint")
      with open("/athina/chroot/tmp/exec","w") as f:
        f.write(exefile)
      os.chmod("/athina/chroot/tmp/exec",0755)
      print "run"
      res = subprocess.Popen(["runner",
        "--root=/athina/chroot", "--work-dir=/tmp", "--env=empty",
        "--setuid="+str(athinauid), "--setgid="+str(athinagid),
        "--max-realtime="+str(15*int(tle)), "--max-cputime="+str(10*int(tle)), "--max-memory="+str(mem),
        "--max-threads=1", "--max-files=4",
        "--stdin=/athina/chroot/in",
        "--stdout=/athina/chroot/out", "--trunc-stdout",
        "--stderr=/dev/null",
        "--memlock",
        "--priority=30",
        "/tmp/exec"], stdout = subprocess.PIPE).communicate()[0];
      print "RES : "+res
      ret = res.split()[0]
      print "RET : "+ret
      judge.log += " ".join(res.split()) + "\n"
      if ret != "OK":
        judge.result = ret
        break
      if checkfile == "":
        ret = subprocess.call(["diff", "-q", "-w", "/athina/chroot/hint", "/athina/chroot/out"])
        if ret != 0:
          judge.result = "ANS"
          break
      else:
        with open("/athina/chroot/tmp/exec","w") as f:
          f.write(checkfile)
        os.chmod("/athina/chroot/tmp/exec",0755)
        ret = subprocess.call(["runner", "--quiet",
          "--root=/athina/chroot", "--work-dir=/tmp", "--env=empty",
          "--setuid="+str(athinauid), "--setgid="+str(athinagid),
          "--max-realtime=60000", "--max-cputime=60000", "--max-memory="+str(256*1024*1024),
          "--max-threads=1", "--max-files=7",
          "--priority=30",
          "/tmp/exec", "/in", "/hint", "/out"])
        if ret != 0:
          judge.result = "ANS"
          break
    except:
      logging.warning("Test failed")
#          pass
    finally:
      subprocess.call(["mkchroot", "-D", "/athina/chroot"], stdout = open("/dev/null", "w"), stderr = subprocess.STDOUT)
