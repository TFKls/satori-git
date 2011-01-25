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
from optparse import OptionParser

parser = OptionParser()

parser.add_option('-d', '--debug', dest='debug', default='', action='store', type='string')

parser.add_option('-L', '--login', dest='login', default='checker', action='store', type='string')
parser.add_option('-P', '--password', dest='password', default='checker', action='store', type='string')

parser.add_option('--jail-dir', dest='jail_dir', default='/jail', action='store', type='string')
parser.add_option('--cgroup-dir', dest='cgroup_dir', default='/cgroup', action='store', type='string')
parser.add_option('--template-dir', dest='template_dir', default='/template', action='store', type='string')
parser.add_option('--template-src', dest='template_src', default='student.tcs.uj.edu.pl:/exports/judge', action='store', type='string')

parser.add_option('--retry-time', dest='retry_time', default=5, action='store', type='int')

parser.add_option('--cgroup', dest='cgroup', default='runner', action='store', type='string')
parser.add_option('--memory', dest='cgroup_memory', default=2*1024*1024, action='store', type='int')
parser.add_option('--time', dest='cgroup_time', default=5*60*1000, action='store', type='int')

parser.add_option('--judge', dest='default_judge', default='/bin/judge', action='store', type='string')

parser.add_option('--host-interface', dest='host_eth', default='vethsh', action='store', type='string')
parser.add_option('--host-ip', dest='host_ip', default='192.168.100.101', action='store', type='string')
parser.add_option('--guest-interface', dest='guest_eth', default='vethsg', action='store', type='string')
parser.add_option('--guest-ip', dest='guest_ip', default='192.168.100.102', action='store', type='string')
parser.add_option('--netmask', dest='netmask', default='255.255.255.0', action='store', type='string')
parser.add_option('--port', dest='control_port', default=8765, action='store', type='int')

(options, args) = parser.parse_args()

def judge_loop():
    while True:
        try:
            token_container.set_token(Machine.authenticate(options.login, options.password))
        except (TokenInvalid, TokenExpired):
            token_container.set_token('')
            continue
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
            if 'template' in td and not td['template'].is_blob:
                template = td['template'].value

            jb = JailBuilder(
                root=options.jail_dir,
                template=template,
                template_path=options.template_dir)
            try:
                jb.create()
                dst_path = os.path.join(jail_dir, 'judge')
                if 'judge' in td and td['judge'].is_blob:
                    td.get_blob_path('judge', dst_path)
                else:
                    with open(options.default_judge, 'r') as judge_src:
                        with open(dst_path, 'w') as judge_dst:
                            shutil.copyfileobj(judge_src, judge_dst)
                os.chmod(dst_path, stat.S_IREAD | stat.S_IEXEC)
                jr = JailRun(
                    submit=sub,
                    root=options.jail_dir,
                    cgroup_path=options.cgroup_dir,
                    template_path=options.template_dir,
                    path='/judge',
                    debug=options.debug,
                    cgroup=options.cgroup,
                    cgroup_memory=options.cgroup_memory,
                    cgroup_time=options.cgroup_time,
                    host_eth=options.host_eth,
                    host_ip=options.host_ip,
                    guest_eth=options.guest_eth,
                    guest_ip=options.guest_ip,
                    netmask=options.netmask,
                    control_port=options.control_port,
                    args = ['--control-host', options.host_ip, '--control-port', str(options.control_port)])
                res = jr.run()
                if options.debug:
                    dh = anonymous_blob_path(options.debug)
                    res['judge.log'] = {'is_blob':True, 'value':dh, 'filename': 'judge.log'}
                Judge.set_result(tr, res)
            except:
                traceback.print_exc()
            finally:
                jb.destroy()
        else:
            time.sleep(options.retry_time)

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

    subprocess.call(['umount', '-l', options.cgroup_dir])
    subprocess.call(['rmdir', options.cgroup_dir])
    subprocess.check_call(['mkdir', '-p', options.cgroup_dir])
    subprocess.check_call(['mount', '-t', 'cgroup', '-o', 'rw,nosuid,noexec,relatime,memory,cpuacct,cpuset', 'cgroup', options.cgroup_dir])
    if options.template_src:
        subprocess.call(['umount', '-l', options.template_dir])
        subprocess.call(['rmdir', options.template_dir])
        subprocess.check_call(['mkdir', '-p', options.template_dir])
        subprocess.check_call(['mkdir', '-p', options.template_dir+'.temp'])
        subprocess.check_call(['mount', options.template_src, templates_dir+'.temp'])
        subprocess.check_call(['rsync', '-a', options.template_dir+'.temp/', templates_dir])
        subprocess.check_call(['umount', options.template_dir+'.temp'])
        subprocess.call(['rmdir', options.template_dir+'.temp'])

def judge_finalize():
        subprocess.call(['umount', '-l', options.cgroup_dir])
        subprocess.call(['rmdir', options.cgroup_dir])
        if options.template_src:
            subprocess.call(['umount', '-l', options.template_dir])
            subprocess.call(['rmdir', options.template_dir])

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
