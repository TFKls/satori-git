#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

#@<checker name="Judge with input generation and verification">
#@      <input>
#@              <param type="time" name="time" description="Time limit" required="true" default="10s"/>
#@              <param type="size" name="memory" description="Memory limit" required="true" default="256MB"/>
#@              <param type="size" name="stack" description="Stack limit" required="false"/>
#@              <param type="blob" name="tools" description="Compilation of tools environment (zip file)" required="false"/>
#@              <param type="blob" name="input" description="Input specification" required="false"/>
#@              <param type="blob" name="generator" description="Input generator" required="false"/>
#@              <param type="blob" name="verifier" description="Input verifier" required="false"/>
#@              <param type="blob" name="hinter" description="Hint generator" required="false"/>
#@              <param type="blob" name="checker" description="Checker" required="false"/>
#@              <param type="text" name="languages" description="Accepted languages (comma separated list of c,cpp,cs,pas,go,java,py,zip)" required="true" default="cpp"/>
#@              <param type="blob" name="environment" description="Compilation environment (zip file)" required="false"/>
#@      </input>
#@      <output>
#@              <param type="text" name="status" description="Status"/>
#@              <param type="blob" name="compile_log" description="Compilation log"/>
#@              <param type="time" name="execute_time_real" description="Execution time"/>
#@              <param type="time" name="execute_time_cpu" description="Execution CPU time"/>
#@              <param type="size" name="execute_memory" description="Execution memory"/>
#@              <param type="blob" name="tools_log" description="Tools log"/>
#@              <param type="blob" name="debug_log" description="Debug log"/>
#@      </output>
#@</checker>

import math
import os
import subprocess
import sys
import traceback
from urllib.parse import urlparse, urlencode, parse_qsl
from urllib.request import urlopen, Request as urlrequest

RUND_HOST, RUND_PORT = os.environ['SATORI_RUND'].split(':')[0:2]
TESTD_HOST, TESTD_PORT = os.environ['SATORI_TESTD'].split(':')[0:2]
TESTD_SESSION = os.environ['SATORI_TESTD_SESSION']

def parse_time(timestr):
    mul = 0.001
    timestr = timestr.strip().lower()
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
    memstr = memstr.strip().lower()
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

source_size = 100*1024
binary_size = 10*1024*1024
compile_time = 20*1000
compile_memory = 1024*1024*1024
compile_stack = 64*1024*1024
tool_time = 60*1000
tool_memory = 1024*1024*1024
tool_stack = 256*1024*1024

def communicate(command, args={}):
    command = command.strip('/ ')
    args['session_id'] = TESTD_SESSION
    with urlopen('http://'+TESTD_HOST+':'+str(TESTD_PORT)+'/'+command+'?'+urlencode(args)) as f:
        return dict(parse_qsl(f.read().decode('utf-8')))

def communicate_get(path, command):
    args = dict()
    command = command.strip('/ ')
    args['session_id'] = TESTD_SESSION
    with urlopen('http://'+TESTD_HOST+':'+str(TESTD_PORT)+'/'+command+'?'+urlencode(args)) as f:
        with open(path, 'wb') as t:
            t.write(f.read())

def communicate_put(path, command, filename=None):
    args = dict()
    command = command.strip('/ ')
    if filename:
        filename = filename.strip('/ ')
    args['session_id'] = TESTD_SESSION
    if filename is None:
        filename = os.path.basename(path)
    with open(path, 'rb') as f:
        req = urlrequest(url='http://'+TESTD_HOST+':'+str(TESTD_PORT)+'/'+command+'/'+filename+'?'+urlencode(args), method='PUT', data=f.read())
        urlopen(req)

def tool_run(name, cmd, stdin='/dev/null', stdout=False, stderr=False, truncate_stdout=False, truncate_stderr=False):
    if not stdout:
        stdout='secure/'+str(name)+'.log'
    logfile = stdout
    if not stderr:
        stderr='__STDOUT__'
    else:
        logfile=stderr
    with open(logfile, 'a') as lf:
        lf.write('--== '+name+' ==--\n')
    tools_run = [ 'satori_run',
          '--work-dir=tool',
          '--env=simple',
          '--max-real-time='+str(tool_time),
          '--max-cpu-time='+str(tool_time),
          '--max-memory='+str(tool_memory),
          '--max-stack='+str(tool_stack),
          '--stdin='+stdin,
          '--stdout='+stdout,
          '--stderr='+stderr, ]
    if truncate_stdout:
        tools_run += [ '--trunc-stdout', ]
    if truncate_stderr:
        tools_run += [ '--trunc-stderr', ]
    tools_run += cmd
    ret = subprocess.call(tools_run)
    communicate_put(logfile, 'result/tools_log')
    if ret != 0:
        communicate('result', {'status': 'INT'})
        sys.exit(0)

try:
    os.chdir('/satori_test')
    DIRS = [ ('secure', 0, 0, 0o700),
             ('aux', 0, 0, 0o755),
             ('src', 0, 0, 0o755),
             ('build', 0, 0, 0o755),
             ('bin', 0, 0, 0o755),
             ('tool', 0, 0, 0o755),
    ]

    for d, u, g, r in DIRS:
        os.makedirs(d, exist_ok=True)
        os.chown(d, u, g)
        os.chmod(d, r)

    submit = communicate('submit')
    test   = communicate('test')

    filename     = submit['content']
    if len(filename.split('.')) < 2:
        communicate('result', {'status': 'EXT'})
        sys.exit(0)
    filebase     = '.'.join(filename.split('.')[:-1])
    fileext      = filename.split('.')[-1].lower()
    time_limit   = parse_time(test['time'])
    memory_limit = parse_memory(test['memory'])
    has_stack = 'stack' in test
    if has_stack:
        stack_limit  = parse_memory(test['stack'])

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
        communicate('result', {'status': 'EXT'})
        sys.exit(0)

#COMPILE SOLUTION
    if has_environment:
        communicate_get(environment_file, 'test/environment')
    communicate_get(source_file, 'submit/content')
    if os.stat(source_file).st_size > source_size:
        communicate('result', {'status': 'RUL'})
        sys.exit(0)
    for compiler in compilers:
        compile_run = [ 'satori_run',
              '--env=simple',
              '--user=satori_compile',
              '--group=satori_compile',
              '--max-real-time='+str(compile_time),
              '--max-cpu-time='+str(compile_time),
              '--max-memory='+str(compile_memory),
              '--max-stack='+str(compile_stack),
              '--stdout=secure/compile.log',
              '--stderr=__STDOUT__',
              ]
        compile_run += compiler
        ret = subprocess.call(compile_run)
        if ret != 0:
            communicate_put('secure/compile.log', 'result/compile_log')
            communicate('result', {'status': 'CME'})
            sys.exit(0)
    communicate_put('secure/compile.log', 'result/compile_log')
    if not os.path.exists(exec_file):
        communicate('result', {'status': 'CME'})
        sys.exit(0)
    if os.stat(exec_file).st_size > binary_size:
        communicate('result', {'status': 'RUL'})
        sys.exit(0)

    has_tools = 'tools' in test
    if has_tools:
        tools_file = '/satori_test/aux/tools.zip'
        tools_inject = [ '7z', 'x', '-o.', tools_file ]
    else:
        tools_file = '/dev/null'
        tools_inject = [ 'true' ]
    if has_tools:
        communicate_get(tools_file, 'test/tools')
        tool_run('inject', tools_inject, stderr='secure/tools.log')

    has_generator = 'generator' in test

#COMPILE INPUT GENERATOR
    if has_generator:
        communicate_get('tool/generator.cpp', 'test/generator')
        tool_run('generator_compile', [ 'g++', '-std=c++0x', '-static', '-O2', 'generator.cpp', '-ogenerator.x'], stderr='secure/tools.log')
    
    has_generator_spec  = 'input' in test

#GENERATE INPUT
    if has_generator_spec:
        communicate_get('secure/data.spec', 'test/input')
        generator_spec_file = 'secure/data.spec'
    else:
        generator_spec_file = '/dev/null'
    if has_generator:
        generator_run = [ './generator.x' ]
    else:
        generator_run = [ 'cat' ]
    tool_run('generator', generator_run, stdin=generator_spec_file, stdout='secure/data.in', truncate_stdout=True, stderr='secure/tools.log')

    has_verifier  = 'verifier' in test

#COMPILE VERIFIER
    if has_verifier:
        communicate_get('tool/verifier.cpp', 'test/verifier')
        tool_run('verifier_compile', [ 'g++', '-std=c++0x', '-static', '-O2', 'verifier.cpp', '-overifier.x'], stderr='secure/tools.log')

#VERIFY INPUT FILE
    if has_verifier:
        tool_run('verifier', [ './verifier.x' ], stdin='secure/data.in', stdout='secure/tools.log')

#EXECUTE SOLUTION
    execute_run = [ 'satori_run', '--log-level=debug',
          '--env=simple',
          '--user=satori_execute',
          '--group=satori_execute',
          '--max-real-time='+str(int(1.5*time_limit)),
          '--max-cpu-time='+str(time_limit),
          '--max-memory='+str(memory_limit),
          '--max-cpus=1',
          '--stdin=secure/data.in',
          '--stdout=secure/data.out', '--trunc-stdout',
          '--stderr=/dev/null',
          ]
    if has_stack:
        execute_run += [
          '--max-stack='+str(stack_limit),
        ]
    if fileext == 'java':
        xss='-Xss'+str(memory_limit/2/(1024**2))+'M'
        xms='-Xms'+str(memory_limit/2/(1024**2))+'M'
        xmx='-Xmx'+str(memory_limit/(1024**2))+'M'
        execute_run += [ 'java', xss, xms, xmx, '-jar', exec_file ]
    elif fileext == 'py':
        execute_run += [ 'python', exec_file ]
    elif fileext == 'cs':
        execute_run += [ 'mono', exec_file ]
    else:
        execute_run += [ './'+exec_file ]
    res = subprocess.Popen(execute_run, stdout = subprocess.PIPE).communicate()[0].decode('utf-8')
    stats = {}
    for line in res.splitlines():
        key = line.split(':')[0].strip().lower()
        value = u':'.join(line.split(':')[1:]).strip()
        stats[key] = value
    communicate('result', {'execute_time_real': stats['time']+'s',
        'execute_time_cpu': stats['cpu']+'s',
        'execute_memory': stats['memory']+'B'})
    ret = stats['result']
    if ret != 'OK':
        communicate('result', {'status': ret})
        sys.exit(0)

    has_hinter = 'hinter' in test

#COMPILE HINT GENERATOR
    if has_hinter:
        communicate_get('tool/hinter.cpp', 'test/hinter')
        tool_run('hinter_compile', [ 'g++', '-std=c++0x', '-static', '-O2', 'hinter.cpp', '-ohinter.x'], stderr='secure/tools.log')

#GENERATE HINT
    if has_hinter:
        tool_run('hinter', [ './hinter.x' ], stdin='secure/data.in', stdout='secure/data.hint', truncate_stdout=True, stderr='secure/tools.log')

    has_checker = 'checker' in test

#COMPILE CHECKER
    if has_checker:
        communicate_get('tool/checker.cpp', 'test/checker')
        tool_run('checker_compile', [ 'g++', '-std=c++0x', '-static', '-O2', 'checker.cpp', '-ochecker.x'], stderr='secure/tools.log')

#CHECK OUTPUT
    if has_hinter:
        hint_file = 'secure/data.hint'
    else:
        hint_file = '/dev/null'
    if has_checker:
        checker = [ 'tool/checker.x', 'secure/data.in', hint_file, 'secure/data.out' ]
    else:
        checker = [ 'diff', '-q', '-w', '-B', hint_file, 'secure/data.out' ]
    checker_run = [ 'satori_run',
          '--env=simple',
          '--max-real-time='+str(tool_time),
          '--max-cpu-time='+str(tool_time),
          '--max-memory='+str(tool_memory),
          '--stdout=secure/tools.log',
          '--stderr=__STDOUT__',
          ]
    checker_run += checker
    ret = subprocess.call(checker_run)
    communicate_put('secure/tools.log', 'result/tools_log')
    if ret != 0:
        communicate('result', {'status': 'ANS'})
        sys.exit(0)

#CHECK LANGUAGE
    has_languages = 'languages' in test
    if has_languages:
        languages = [ l.strip().lower() for l in test['languages'].split(',') ]
        if fileext not in languages:
            communicate('result', {'status': 'LANG'})
            sys.exit(0)

    communicate('result', {'status': 'OK'})

except:
    sys.stderr.close()
    with open('secure/debug.log', 'a') as d:
        traceback.print_exc(file=d)
    communicate_put('secure/debug.log', 'result/debug_log')
