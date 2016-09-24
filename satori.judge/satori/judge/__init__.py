# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

from satori.judge.judge import JailBuilder, JailRun
from satori.client.common import want_import

import os
import resource
import stat
import sys
import shutil
import time
import subprocess
import traceback

from satori.tools import options, setup, authenticate

options.add_argument('--debug', dest='debug', default='')

options.add_argument('--jail-dir', dest='jail_dir', default='/jail')
options.add_argument('--cgroup-dir', dest='cgroup_dir', default='/sys/fs/cgroup')
options.add_argument('--template-dir', dest='template_dir', default='/template')
options.add_argument('--template-src', dest='template_src', default='student.tcs.uj.edu.pl:/exports/judge')

options.add_argument('--retry-time', dest='retry_time', default=5, type=int)

options.add_argument('--cgroup', dest='cgroup', default='runner')
options.add_argument('--memory', dest='cgroup_memory', default=8*1024*1024*1024, type=int)
options.add_argument('--time', dest='real_time', default=5*60*1000, type=int)

options.add_argument('--host-interface', dest='host_eth', default='vethsh')
options.add_argument('--host-ip', dest='host_ip', default='192.168.100.101')
options.add_argument('--guest-interface', dest='guest_eth', default='vethsg')
options.add_argument('--guest-ip', dest='guest_ip', default='192.168.100.102')
options.add_argument('--netmask', dest='netmask', default='255.255.255.0')
options.add_argument('--port', dest='control_port', default=8765, type=int)

def judge_loop():
    while True:
        authenticate()
        submit = Judge.get_next()
        if submit != None:
            tr = submit['test_result']
            td = OaMap(submit['test_data'])
            sd = OaMap(submit['submit_data'])

            sub = {
                'test_data' : td,
                'submit_data' : sd,
            }

            template = 'default'
            if td.get('template') and not td.get('template').is_blob:
                template = str(td.get('template').value)

            jb = JailBuilder(
                root=option_values.jail_dir,
                template=template,
                template_path=option_values.template_dir)
            try:
                jb.create()
                dst_path = os.path.join(jb.jail_path, 'judge')
                if td.get('judge') and td.get('judge').is_blob:
                    td.get_blob_path('judge', dst_path)
                    os.chmod(dst_path, stat.S_IREAD | stat.S_IEXEC)
                else:
                    res = dict()
                    res['status'] = {'is_blob':False, 'value':'INT'}
                    res['description'] = {'is_blob':False, 'value':'No judge specified'}
                    Judge.set_result(tr, res)
                    continue
                jr = JailRun(
                    submit=sub,
                    root=jb.jail_path,
                    cgroup_path=option_values.cgroup_dir,
                    template_path=option_values.template_dir,
                    path='/judge',
                    debug=option_values.debug,
                    cgroup=option_values.cgroup,
                    cgroup_memory=option_values.cgroup_memory,
                    real_time=option_values.real_time,
                    host_eth=option_values.host_eth,
                    host_ip=option_values.host_ip,
                    guest_eth=option_values.guest_eth,
                    guest_ip=option_values.guest_ip,
                    netmask=option_values.netmask,
                    control_port=option_values.control_port,
                    args = ['--control-host', option_values.host_ip, '--control-port', str(option_values.control_port)])
                res = jr.run()
                Judge.set_result(tr, res)
            except:
                traceback.print_exc()
            finally:
                jb.destroy()
        else:
            time.sleep(option_values.retry_time)

def judge_initialize():
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

    if option_values.template_src:
        subprocess.call(['umount', '-l', option_values.template_dir])
        subprocess.call(['rmdir', option_values.template_dir])
        subprocess.check_call(['mkdir', '-p', option_values.template_dir])
        subprocess.check_call(['mkdir', '-p', option_values.template_dir+'.temp'])
        subprocess.check_call(['mount', option_values.template_src, option_values.template_dir+'.temp'])
        subprocess.check_call(['rsync', '-a', option_values.template_dir+'.temp/', option_values.template_dir])
        subprocess.check_call(['umount', option_values.template_dir+'.temp'])
        subprocess.call(['rmdir', option_values.template_dir+'.temp'])

def judge_finalize():
        if option_values.template_src:
            subprocess.call(['umount', '-l', option_values.template_dir])
            subprocess.call(['rmdir', option_values.template_dir])

def judge_init():
    want_import(globals(), '*')
    global option_values
    option_values = setup()
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
