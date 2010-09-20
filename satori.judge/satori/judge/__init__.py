# vim:ts=4:sts=4:sw=4:expandtab
from satori.judge.judge import run_server, JailBuilder, JailRun
import time
import subprocess

jail_dir = '/jail'
cgroup_dir = '/cgroup'
templates_dir = '/templates'
templates_src = 'student.tcs.uj.edu.pl:/exports/judge/templates'

def judge_try():
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
        jr = JailRun(root=jail_dir, path='bash', search=True)
        jr.run()
    finally:
        jb.destroy()

def judge_loop():
    from satori.client.common.remote import Judge
    while True:
        submit = Judge.get_next()
        if submit != None:
            tr = submit['test_result']
            t = tr.test
            s = tr.submit
            td = submit['test_contents']
            sd = submit['submit_contents']

            template=td.get('template', 'default')

            jb = JailBuilder(root=jail_dir, template=template, template_path=templates_dir)
            try:
                jb.create()
                t.oa_get_blob('judge', os.path.join(jail_dir, 'judge')) #TODO Testy bokiem - t nie dziala.
                jr = JailRun(submit=submit, root=jail_dir, path='/judge')
                jr.run()
            finally:
                jb.destroy()
        else:
            time.sleep(5)
        
def judge_init():
    if False:
        subprocess.check_call(['busybox', 'mdev', '-s'])
        subprocess.check_call(['mkdir', '-p', '/dev/pts'])
        subprocess.check_call(['mount', '-t', 'devpts', '-o', 'rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000', 'devpts', '/dev/pts'])
        subprocess.check_call(['ln', '-s', '/proc/self/fd/0', '/dev/stdin'])
        subprocess.check_call(['ln', '-s', '/proc/self/fd/1', '/dev/stdout'])
        subprocess.check_call(['ln', '-s', '/proc/self/fd/2', '/dev/stderr'])
        subprocess.check_call(['/usr/sbin/sshd'])
    subprocess.check_call(['mkdir', '-p', cgroup_dir])
    subprocess.check_call(['mount', '-t', 'cgroup', '-o', 'rw,nosuid,noexec,relatime,memory,cpuacct,cpuset', 'cgroup', cgroup_dir])
    subprocess.check_call(['mkdir', '-p', templates_dir])
    subprocess.check_call(['mount', templates_src, templates_dir])


    subprocess.check_call(['iptables', '-F', 'INPUT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'INVALID', '-j', 'DROP'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'eth+', '-p', 'tcp', '--dport', '22', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'veth+', '-p', 'tcp', '--dport', '8765', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-P', 'INPUT', 'DROP'])

    subprocess.check_call(['iptables', '-F', 'OUTPUT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'INVALID', '-j', 'DROP'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'owner', '--uid-owner', 'root', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'owner', '--uid-owner', 'daemon', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-P', 'OUTPUT', 'DROP'])

    subprocess.check_call(['iptables', '-F', 'FORWARD'])
    subprocess.check_call(['iptables', '-P', 'FORWARD', 'ACCEPT'])

    judge_loop()

    #subprocess.check_call(['reboot', '-f'])
