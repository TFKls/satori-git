# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

from satori.client.common import want_import
want_import(globals(), '*')

import os
import resource
import stat
import sys
import shutil
import time
import subprocess
import traceback

from satori.tools import options, setup, authenticate
options.add_option('--debug', dest='debug', default='', action='store', type='string')

options.add_option('--jail-dir', dest='jail_dir', default='/jail', action='store', type='string')
options.add_option('--cgroup-dir', dest='cgroup_dir', default='/cgroup', action='store', type='string')
options.add_option('--template-dir', dest='template_dir', default='/template', action='store', type='string')
options.add_option('--template-src', dest='template_src', default='student.tcs.uj.edu.pl:/exports/judge', action='store', type='string')

options.add_option('--retry-time', dest='retry_time', default=5, action='store', type='int')

options.add_option('--cgroup', dest='cgroup', default='runner', action='store', type='string')
options.add_option('--memory', dest='cgroup_memory', default=8*1024*1024*1024, action='store', type='int')
options.add_option('--time', dest='real_time', default=5*60*1000, action='store', type='int')

options.add_option('--host-interface', dest='host_eth', default='vethsh', action='store', type='string')
options.add_option('--host-ip', dest='host_ip', default='192.168.100.101', action='store', type='string')
options.add_option('--guest-interface', dest='guest_eth', default='vethsg', action='store', type='string')
options.add_option('--guest-ip', dest='guest_ip', default='192.168.100.102', action='store', type='string')
options.add_option('--netmask', dest='netmask', default='255.255.255.0', action='store', type='string')
options.add_option('--port', dest='control_port', default=8765, action='store', type='int')

(options, args) = setup()

def cribfinder_loop():
    while True:
        authenticate()
        print "Kurwa"
        comparisons = Comparison.filter(ComparisonStruct(execution_date=None))
        #comparisons = Comparison.filter()
        for comp in comparisons:
            print comp.regexp
            test_suite_res = TestSuiteResult.filter(TestSuiteResultStruct(test_suite=comp.test_suite, status=comp.regexp))
            num = 0;
            submits = []
            for tsr in test_suite_res:
                submit = Web.get_result_details(submit=tsr.submit)
                submits.append(submit)
                filetmp = open('tmp/'+str(num)+'.cpp', 'w')
                num += 1
                filetmp.write(submit.data)
                filetmp.close() 
            for i in range(0,num-2):
                for j in rnage(i+1,num-1):
                    result = compere('tmp/'+str(i)+'.cpp','tmp/'+str(j)+'.cpp',100)
                    
            compres = ComparisonResult()
            ComparisonResult.modify(compres,scomparison=comp, submit_1 = submits[0], submit_2 = submits[1],result = 999.9)
            comp.modify(comp)
            break
            #print comp.execution_date
        print "End of test"
        break

        

def cribfinder_initialize():
    for res in [ resource.RLIMIT_CPU, resource.RLIMIT_FSIZE, resource.RLIMIT_DATA, resource.RLIMIT_STACK, resource.RLIMIT_RSS, resource.RLIMIT_NPROC, resource.RLIMIT_MEMLOCK, resource.RLIMIT_AS ]:
        resource.setrlimit(res, (-1,-1))
    subprocess.check_call(['iptables', '-P', 'INPUT', 'ACCEPT'])
    subprocess.check_call(['iptables', '-F', 'INPUT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'INVALID', '-j', 'DROP'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'eth+', '-p', 'tcp', '--dport', '22', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'veth+', '-p', 'tcp', '--dport', '8765', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-j', 'LOG'])
    subprocess.check_call(['iptables', '-P', 'INPUT', 'ACCEPT'])

    subprocess.check_call(['iptables', '-P', 'OUTPUT', 'ACCEPT'])
    subprocess.check_call(['iptables', '-F', 'OUTPUT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'INVALID', '-j', 'DROP'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'owner', '--uid-owner', 'root', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'owner', '--uid-owner', 'daemon', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-j', 'LOG'])
    subprocess.check_call(['iptables', '-P', 'OUTPUT', 'ACCEPT'])

    subprocess.check_call(['iptables', '-P', 'FORWARD', 'ACCEPT'])
    subprocess.check_call(['iptables', '-F', 'FORWARD'])
    subprocess.check_call(['iptables', '-P', 'FORWARD', 'ACCEPT'])

    subprocess.call(['umount', '-l', options.cgroup_dir])
    subprocess.call(['rmdir', options.cgroup_dir])
    subprocess.check_call(['mkdir', '-p', options.cgroup_dir])
    subprocess.check_call(['mount', '-t', 'cgroup', '-o', 'rw,nosuid,noexec,relatime,memory,cpuacct,cpuset', 'cgroup', options.cgroup_dir])
    if options.template_src:
        subprocess.call(['umount', '-l', options.template_dir])
        subprocess.call(['rmdir', options.template_dir])
        subprocess.check_call(['mkdir', '-p', options.template_dir])
        subprocess.check_call(['mkdir', '-p', options.template_dir+'.temp'])
        subprocess.check_call(['mount', options.template_src, options.template_dir+'.temp'])
        subprocess.check_call(['rsync', '-a', options.template_dir+'.temp/', options.template_dir])
        subprocess.check_call(['umount', options.template_dir+'.temp'])
        subprocess.call(['rmdir', options.template_dir+'.temp'])

def cribfinder_finalize():
        subprocess.call(['umount', '-l', options.cgroup_dir])
        subprocess.call(['rmdir', options.cgroup_dir])
        if options.template_src:
            subprocess.call(['umount', '-l', options.template_dir])
            subprocess.call(['rmdir', options.template_dir])

def cribfinder_init():
    try:
        cribfinder_initialize()
        while True:
            try:
                cribfinder_loop()
            except:
                traceback.print_exc()
            time.sleep(10)
    except:
        traceback.print_exc()
    finally:
        cribfinder_finalize()
cribfinder_loop()
