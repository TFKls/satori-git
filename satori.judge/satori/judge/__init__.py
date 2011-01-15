# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

from satori.judge.judge import JailBuilder, JailRun
from satori.client.common.remote import *

import os
import stat
import sys
import shutil
import time
import subprocess
import traceback

jail_dir = '/jail'
cgroup_dir = '/cgroup'
templates_dir = '/templates'
templates_src = 'student.tcs.uj.edu.pl:/exports/judge'
#templates_src = None
login = 'checker'
secret = 'sekret'
sleep_time = 5
cgroup = 'runner'
cgroup_memory = 512*1024*1024
cgroup_time = 5*60*1000
default_judge = '/bin/judge'
#debug = '/judge.debug.txt'
debug = ''
host_eth = 'vethsh'
host_ip = '192.168.100.101'
guest_eth = 'vethsg'
guest_ip = '192.168.100.102'
netmask = '255.255.255.0'
control_port = 8765



def judge_bash():
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options] DIR")
    parser.add_option("-T", "--template",
        default='default',
        action="store",
        help="Template to use")
    (options, args) = parser.parse_args()
    jb = JailBuilder(root=jail_dir, template=options.template, template_path=templates_dir)
    try:
        jb.create()
        jr = JailRun(submit={}, root=jail_dir, cgroup_path=cgroup_dir, template_path=templates_dir, path='bash', search=True, debug=debug, cgroup=cgroup, cgroup_memory=cgroup_memory, cgroup_time=cgroup_time, host_eth=host_eth, host_ip=host_ip, guest_eth=guest_eth, guest_ip=guest_ip, netmask=netmask, control_port=control_port )
        jr.run()
    except:
        traceback.print_exc()
    finally:
        jb.destroy()

def judge_loop():
    while True:
        try:
            token_container.set_token(Machine.authenticate(login, secret))
        except (TokenInvalid, TokenExpired):
            token_container.set_token('')
            continue
        submit = Judge.get_next()
        if submit != None:
            tr = submit['test_result']
            td = submit['test_data']
            sd = submit['submit_data']

            sub = {
                'test_data' : OaMap(td),
                'submit_data' : OaMap(sd),
            }

            template = 'default'
            if 'judge.template' in td and not td['judge.template']['is_blob']:
                template = td['judge.template']['value']

            jb = JailBuilder(root=jail_dir, template=template, template_path=templates_dir)
            try:
                jb.create()
                dst_path = os.path.join(jail_dir, 'judge')
                if False and 'judge' in td and td['judge']['is_blob']:
                    tr.test.data_get_blob_path('judge', dst_path)
                else:
                    with open(default_judge, 'r') as judge_src:
                        with open(dst_path, 'w') as judge_dst:
                            shutil.copyfileobj(judge_src, judge_dst)
                os.chmod(dst_path, stat.S_IREAD | stat.S_IEXEC)
                jr = JailRun(submit=sub, root=jail_dir, cgroup_path=cgroup_dir, template_path=templates_dir, path='/judge', debug=debug, cgroup=cgroup, cgroup_memory=cgroup_memory, cgroup_time=cgroup_time, host_eth=host_eth, host_ip=host_ip, guest_eth=guest_eth, guest_ip=guest_ip, netmask=netmask, control_port=control_port, args = ['--control-host', host_ip, '--control-port', str(control_port)])
                res = jr.run()
                if debug:
                    dh = anonymous_blob_path(debug)
                    res['judge.log'] = {'is_blob':True, 'value':dh, 'filename': 'judge.log'}
                Judge.set_result(tr, res)
            except:
                traceback.print_exc()
            finally:
                jb.destroy()
        else:
            time.sleep(sleep_time)

def judge_initialize():
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

    subprocess.check_call(['mkdir', '-p', cgroup_dir])
    subprocess.check_call(['mount', '-t', 'cgroup', '-o', 'rw,nosuid,noexec,relatime,memory,cpuacct,cpuset', 'cgroup', cgroup_dir])
    if templates_src:
        subprocess.check_call(['mkdir', '-p', templates_dir])
        subprocess.check_call(['mkdir', '-p', templates_dir+'.temp'])
        subprocess.check_call(['mount', templates_src, templates_dir+'.temp'])
        subprocess.check_call(['rsync', '-a', templates_dir+'.temp', templates_dir])
        subprocess.check_call(['umount', templates_dir+'.temp'])
        subprocess.call(['rmdir', templates_dir+'.temp'])

def judge_finalize():
        subprocess.call(['umount', '-l', cgroup_dir])
        subprocess.call(['rmdir', cgroup_dir])
        if templates_src:
            subprocess.call(['umount', '-l', templates_dir])
            subprocess.call(['rmdir', templates_dir])

def judge_init():
    try:
        judge_initialize()
        while True:
            try:
                judge_loop()
            except:
                traceback.print_exc()
            time.sleep(10)
    except:
        traceback.print_exc()
    finally:
        judge_finalize()

def judge_try():
    try:
        judge_initialize()
        judge_bash()
    except:
        traceback.print_exc()
    finally:
        judge_finalize()

