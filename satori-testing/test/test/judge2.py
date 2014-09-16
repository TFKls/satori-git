#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

#@<checker name="Judge with input generation and verification">
#@      <input>
#@              <param type="time" name="time" description="Time limit" required="true" default="10s"/>
#@              <param type="size" name="memory" description="Memory limit" required="true" default="256MB"/>
#@              <param type="blob" name="tools" description="Compilation of tools environment (zip file)" required="false"/>
#@              <param type="blob" name="input" description="Input specification" required="false"/>
#@              <param type="blob" name="generator" description="Input generator" required="false"/>
#@              <param type="blob" name="verifier" description="Input verifier" required="false"/>
#@              <param type="blob" name="hinter" description="Hint generator" required="false"/>
#@              <param type="blob" name="hint" description="Output specification" required="false"/>
#@              <param type="blob" name="checker" description="Checker" required="false"/>
#@      </input>
#@      <output>
#@              <param type="text" name="status" description="Status"/>
#@              <param type="blob" name="compile_log" description="Compilation log"/>
#@              <param type="time" name="execute_time_real" description="Execution time"/>
#@              <param type="time" name="execute_time_cpu" description="Execution CPU time"/>
#@              <param type="size" name="execute_memory" description="Execution memory"/>
#@              <param type="blob" name="generator_log" description="Input generation log"/>
#@              <param type="blob" name="verifier_log" description="Input verification log"/>
#@              <param type="blob" name="hinter_log" description="Hint generation log"/>
#@              <param type="blob" name="checker_log" description="Checking log"/>
#@              <param type="blob" name="debug_log" description="Debug log"/>
#@      </output>
#@</checker>

import httplib
import math
import os
import shutil
import subprocess
import sys
import traceback
import yaml
from optparse import OptionParser

sys.stderr = open('/tmp/debug.log', 'w')

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

source_size = 100*1024
binary_size = 10*1024*1024
compile_time = 20*1000
compile_memory = 1024*1024*1024
compile_stack = 64*1024*1024
tool_time = 60*1000
tool_memory = 1024*1024*1024
tool_stack = 256*1024*1024

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

def tool_run(name, cmd, stdin='/dev/null', stdout=False, stderr=False, truncate_stdout=False, truncate_stderr=False, log=False):
    if not stdout:
        stdout='/tmp/'+str(name)+'.log'
    logfile = stdout
    if not stderr:
        stderr='__STDOUT__'
    else:
        logfile=stderr
    tools_run = [ 'runner', '--quiet',
          '--root=/jail',
          '--work-dir=/tools',
          '--env=simple',
          '--control-host='+options.host,
          '--control-port='+str(options.port),
          '--cgroup=/tools_'+str(name),
          '--cgroup-cputime='+str(tool_time),
          '--cgroup-memory='+str(tool_memory),
          '--max-realtime='+str(tool_time),
          '--max-stack='+str(tool_stack),
          '--stdin='+stdin,
          '--stdout='+stdout,
          '--stderr='+stderr, ]
    if truncate_stdout:
        tools_run += [ '--trunc-stdout', ]
    if truncate_stderr:
        tools_run += [ '--trunc-stderr', ]
    tools_run += [
          '--priority=30',
          '--search', ]
    tools_run += cmd
    ret = subprocess.call(tools_run)
    if log:
        communicate('SETBLOB', {'name': str(log), 'path': logfile})
    if ret != 0:
        communicate('SETSTRING', {'name': 'status', 'value': 'INT'})
        sys.exit(0)

try:
    submit = communicate('GETSUBMIT', check=False)
    test   = communicate('GETTEST', check=False)

    filename     = os.path.basename(submit['content']['filename'])
    if len(filename.split('.')) < 2:
        communicate('SETSTRING', {'name': 'status', 'value': 'EXT'})
        sys.exit(0)
    filebase     = '.'.join(filename.split('.')[:-1])
    fileext      = filename.split('.')[-1].lower()
    time_limit   = parse_time(test.get('time')['value'])
    memory_limit = parse_memory(test.get('memory')['value'])
    has_stack = 'stack' in test
    if has_stack:
        stack_limit  = parse_memory(test.get('stack')['value'])

    has_environment = 'environment' in test
    if has_environment:
        environment_file = 'aux/environment.zip'
        environment_inject = [ '7z', 'x', '-osrc', environment_file ]
    else:
        environment_file = '/dev/null'
        environment_inject = [ 'true' ]

    if fileext == 'c':
        source_file = 'src/solution.c'
        exec_file = 'bin/solution.x'
        compilers = [
                environment_inject,
                [ 'gcc', '-static', '-O2', '-Wall', source_file, '-lm', '-o'+exec_file ]
        ]
    elif fileext in ['cpp', 'cc', 'cxx']:
        fileext = 'cpp'
        source_file = 'src/solution.cpp'
        exec_file = 'bin/solution.x'
        compilers  = [
                environment_inject,
                [ 'g++', '-std=c++0x', '-static', '-O2', '-Wall', source_file, '-o'+exec_file ]
        ]
    elif fileext == 'cs':
        fileext = 'cs'
        source_file = 'src/'+filebase+'.cs'
        exec_file = 'bin/'+filebase+'.exe'
        compilers = [
                environment_inject,
                [ 'mcs', source_file ],
                [ 'cp', '-a', 'src/'+os.path.basename(exec_file), exec_file ]
        ]
    elif fileext in ['pas', 'p', 'pp']:
        fileext = 'pas'
        source_file = 'src/solution.pas'
        exec_file = 'bin/solution.x'
        compilers  = [
                environment_inject,
                [ 'fpc', '-Sgic', '-Xs', '-viwnh', '-O2', source_file, '-o'+exec_file ]
        ]
    elif fileext == 'go':
        fileext = 'go'
        source_file = 'src/solution.go'
        exec_file = 'bin/solution.x'
        compilers  = [
                environment_inject,
                [ 'gccgo', '-O2', '-Wall', source_file, '-o'+exec_file ]
        ]
    elif fileext == 'java':
        fileext = 'java'
        source_file = 'src/'+filebase+'.java'
        exec_file = 'bin/'+filebase+'.jar'
        xss='-Xss'+str(compile_memory/2/(1024**2))+'M'
        xms='-Xms'+str(compile_memory/2/(1024**2))+'M'
        xmx='-Xmx'+str(compile_memory/(1024**2))+'M'
        compilers = [
                environment_inject,
                [ 'javac', '-J'+xss, '-J'+xms, '-J'+xmx, '-d', 'build', source_file ],
                [ 'jar', '-J'+xss, '-J'+xms, '-J'+xmx, '-cfe', exec_file, filebase, '-C', 'build', '.' ]
        ]
    elif fileext == 'py':
        fileext = 'py'
        source_file = 'src/'+filebase+'.py'
        exec_file = 'bin/'+filebase+'.py'
        compilers = [
                environment_inject,
                [ 'cp', '-a', source_file, exec_file ]
        ]
    elif fileext == 'zip':
        fileext = 'zip'
        source_file = 'aux/solution.zip'
        exec_file = 'bin/solution.x'
        compilers = [
                [ '7z', 'x', '-osrc', source_file ],
                environment_inject,
                [ 'make', '-C', 'src', os.path.basename(exec_file) ],
                [ 'cp', '-a', 'src/'+os.path.basename(exec_file), exec_file ]
        ]
    else:
        communicate('SETSTRING', {'name': 'status', 'value': 'EXT'})
        sys.exit(0)

    template = 'judge'
    communicate('CREATEJAIL', {'path': '/jail', 'template': template})

#COMPILE SOLUTION
    for d in [ 'src', 'build', 'bin', 'aux' ]:
        if not os.path.exists(os.path.join('/jail/runner', d)):
            os.makedirs(os.path.join('/jail/runner', d))
        os.chmod(os.path.join('/jail/runner', d), 0777)
    if has_environment:
        communicate('GETTESTBLOB', {'name': 'environment', 'path': os.path.join('/jail/runner', environment_file)})
    communicate('GETSUBMITBLOB', {'name': 'content', 'path': os.path.join('/jail/runner', source_file)})
    if os.stat(os.path.join('/jail/runner', source_file)).st_size > source_size:
        communicate('SETSTRING', {'name': 'status', 'value': 'RUL'})
        sys.exit(0)
    for compiler in compilers:
        compile_run = [ 'runner', '--quiet',
              '--root=/jail',
              '--work-dir=/runner',
              '--env=simple',
              '--setuid=runner',
              '--setgid=runner',
              '--control-host='+options.host,
              '--control-port='+str(options.port),
              '--cgroup=/compile',
              '--cgroup-cputime='+str(compile_time),
              '--max-realtime='+str(compile_time),
              '--stdout=/tmp/compile.log',
              '--stderr=__STDOUT__',
              '--priority=30']
        if fileext == 'java':
            compile_run += [
              '--cgroup-memory='+str(compile_memory*3/2+32*1024*1024) ]
        else:
            compile_run += [
              '--cgroup-memory='+str(compile_memory),
              '--max-stack='+str(compile_stack) ]
        compile_run += [ '--search' ] + compiler
        ret = subprocess.call(compile_run)
        if ret != 0:
            communicate('SETBLOB', {'name': 'compile_log', 'path': '/tmp/compile.log'})
            communicate('SETSTRING', {'name': 'status', 'value': 'CME'})
            sys.exit(0)
    communicate('SETBLOB', {'name': 'compile_log', 'path': '/tmp/compile.log'})
    if not os.path.exists(os.path.join('/jail/runner', exec_file)):
        communicate('SETSTRING', {'name': 'status', 'value': 'CME'})
        sys.exit(0)
    if os.stat(os.path.join('/jail/runner', exec_file)).st_size > binary_size:
        communicate('SETSTRING', {'name': 'status', 'value': 'RUL'})
        sys.exit(0)
    for d in [ 'src', 'build', 'aux' ]:
        if os.path.exists(os.path.join('/jail/runner', d)):
            shutil.rmtree(os.path.join('/jail/runner', d))

    has_tools = 'tools' in test
    if has_tools:
        tools_file = 'aux/tools.zip'
        tools_inject = [ '7z', 'x', '-osrc', tools_file ]
    else:
        tools_file = '/dev/null'
        tools_inject = [ 'true' ]
    for d in [ 'src', 'bin', 'aux' ]:
        if not os.path.exists(os.path.join('/jail/tools', d)):
            os.makedirs(os.path.join('/jail/tools', d))
        os.chmod(os.path.join('/jail/tools', d), 0750)
    if has_tools:
        communicate('GETTESTBLOB', {'name': 'tools', 'path': os.path.join('/jail/tools', tools_file)})
        tool_run('inject', tools_inject)

    has_generator = 'generator' in test

#COMPILE INPUT GENERATOR
    if has_generator:
        has_generator_name = 'filename' in test.get('generator')
        has_python_generator = has_generator_name and test.get('generator')['filename'].endswith('.py')
        if has_python_generator:
            communicate('GETTESTBLOB', {'name': 'generator', 'path': '/jail/tools/bin/generator.x'})
            tool_run('generator_compile', [ 'chmod', '+x', 'bin/generator.x'], log='generator_log')
        else:
            communicate('GETTESTBLOB', {'name': 'generator', 'path': '/jail/tools/src/generator.cpp'})
            tool_run('generator_compile', [ 'g++', '-std=c++0x', '-static', '-O2', 'src/generator.cpp', '-obin/generator.x'], stdout='/tmp/generator.log', log='generator_log')
    
    has_generator_spec  = 'input' in test

#GENERATE INPUT
    if has_generator_spec:
        communicate('GETTESTBLOB', {'name': 'input', 'path': '/tmp/data.spec'})
        generator_spec_file = '/tmp/data.spec'
    else:
        generator_spec_file = '/dev/null'
    if has_generator:
        generator_run = [ 'bin/generator.x' ]
    else:
        generator_run = [ 'cat' ]
    tool_run('generator', generator_run, stdin=generator_spec_file, stdout='/tmp/data.in', truncate_stdout=True, stderr='/tmp/generator.log', log='generator_log')


    has_verifier  = 'verifier' in test

#COMPILE VERIFIER
    if has_verifier:
        communicate('GETTESTBLOB', {'name': 'verifier', 'path': '/jail/tools/src/verifier.cpp'})
        tool_run('verifier_compile', [ 'g++', '-std=c++0x', '-static', '-O2', 'src/verifier.cpp', '-obin/verifier.x'], stdout='/tmp/verifier.log', log='verifier_log')

#VERIFY INPUT FILE
    if has_verifier:
        tool_run('verifier', [ 'bin/verifier.x' ], stdin='/tmp/data.in', stdout='/tmp/verifier.log', log='verifier_log')

#RUN SOLUTION
    execute_run = [ 'runner',
          '--root=/jail',
          '--work-dir=/runner',
          '--env=empty',
          '--setuid=runner',
          '--setgid=runner',
          '--control-host='+options.host,
          '--control-port='+str(options.port),
          '--cgroup=/execute',
          '--cgroup-cputime='+str(time_limit),
          '--cpus=0',
          '--max-cputime='+str(time_limit),
          '--max-realtime='+str(int(1.5*time_limit)),
          '--stdin=/tmp/data.in',
          '--stdout=/tmp/data.out', '--trunc-stdout',
          '--stderr=/dev/null',
          '--priority=30']
    if has_stack:
        execute_run += [
          '--max-stack='+str(stack_limit),
        ]
    if fileext == 'java':
        execute_run += [
          '--cgroup-memory='+str(memory_limit*3/2+32*1024*1024),
        ]
        xss='-Xss'+str(memory_limit/2/(1024**2))+'M'
        xms='-Xms'+str(memory_limit/2/(1024**2))+'M'
        xmx='-Xmx'+str(memory_limit/(1024**2))+'M'
        execute_run += [ '--search', 'java', xss, xms, xmx, '-jar', exec_file ]
    elif fileext == 'py':
        execute_run += [
          '--cgroup-memory='+str(memory_limit),
        ]
        execute_run += [ '--search', 'python', exec_file ]
    elif fileext == 'cs':
        execute_run += [
          '--cgroup-memory='+str(memory_limit),
        ]
        execute_run += [ '--search', 'mono', exec_file ]
    elif fileext == 'zip':
        execute_run += [
          '--cgroup-memory='+str(memory_limit),
        ]
        execute_run += [ './' + exec_file ]
    else:
        execute_run += [
          '--cgroup-memory='+str(memory_limit),
        ]
        execute_run += [ './' + exec_file ]
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
    if ret not in [ 'OK', 'TLE', 'RTE' ]:
        ret = 'RTE'
    if ret != 'OK':
        communicate('SETSTRING', {'name': 'status', 'value': ret})
        sys.exit(0)

    has_hinter = 'hinter' in test

#COMPILE HINT GENERATOR
    if has_hinter:
        communicate('GETTESTBLOB', {'name': 'hinter', 'path': '/jail/tools/src/hinter.cpp'})
        tool_run('hinter_compile', [ 'g++', '-std=c++0x', '-static', '-O2', 'src/hinter.cpp', '-obin/hinter.x'], stdout='/tmp/hinter.log', log='hinter_log')

#GENERATE HINT
    if has_hinter:
        tool_run('hinter', [ 'bin/hinter.x' ], stdin='/tmp/data.in', stdout='/tmp/data.hint', truncate_stdout=True, stderr='/tmp/hinter.log', log='hinter_log')

    has_checker = 'checker' in test

#COMPILE CHECKER
    if has_checker:
        communicate('GETTESTBLOB', {'name': 'checker', 'path': '/jail/tools/src/checker.cpp'})
        tool_run('checker_compile', [ 'g++', '-std=c++0x', '-static', '-O2', 'src/checker.cpp', '-obin/checker.x'], stdout='/tmp/checker.log', log='checker_log')

#CHECK OUTPUT
    if has_hint or has_hinter:
        hint_file = '/tmp/data.hint'
    else:
        hint_file = '/dev/null'
    if has_checker:
        checker = [ '/jail/tools/bin/checker.x', '/tmp/data.in', hint_file, '/tmp/data.out' ]
    else:
        checker = [ 'diff', '-q', '-w', '-B', hint_file, '/tmp/data.out' ]
    checker_run = [ 'runner', '--quiet',
          '--root=/',
          '--work-dir=/',
          '--env=simple',
          '--control-host='+options.host,
          '--control-port='+str(options.port),
          '--cgroup=/tools_checker',
          '--cgroup-memory='+str(tool_memory),
          '--cgroup-cputime='+str(tool_time),
          '--max-realtime='+str(tool_time),
          '--stdout=/tmp/checker.log',
          '--stderr=__STDOUT__',
          '--priority=30',
          '--search', ]
    checker_run += checker
    ret = subprocess.call(checker_run)
    communicate('SETBLOB', {'name': 'checker_log', 'path': '/tmp/checker.log'})
    if ret != 0:
        communicate('SETSTRING', {'name': 'status', 'value': 'ANS'})
        sys.exit(0)

    communicate('SETSTRING', {'name': 'status', 'value': 'OK'})

except:
    sys.stderr.close()
    with open('/tmp/debug.log', 'a') as d:
        traceback.print_exc(file=d)
    communicate('SETBLOB', {'name': 'debug_log', 'path': '/tmp/debug.log'})
