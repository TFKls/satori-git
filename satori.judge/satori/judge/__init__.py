# vim:ts=4:sts=4:sw=4:expandtab
from satori.judge.judge import run_server, JailBuilder, JailRun
import time
import subprocess
import traceback

jail_dir = '/jail'
cgroup_dir = '/cgroup'
templates_dir = '/templates'
templates_src = 'student.tcs.uj.edu.pl:/exports/judge/templates'
secret = 'sekret'
sleep_time = 5

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
        jr = JailRun(root=jail_dir, path='bash', search=True)
        jr.run()
    except:
        traceback.print_exc()
    finally:
        jb.destroy()

def judge_loop():
    from satori.client.common.remote import token_container, Security, Judge
    token_container.set_token(Security.machine_login(secret))
    while True:
        print 'fetch'
        submit = Judge.get_next()
        if submit != None:
            print 'hello'
            continue
            tr = submit['test_result']
            td = submit['test_contents']
            sd = submit['submit_contents']

            template=td.get('template', 'default')

            jb = JailBuilder(root=jail_dir, template=template, template_path=templates_dir)
            try:
                jb.create()
                #judge_src = tr.test.data_get_blob('judge')
                judge_src = open('/bin/ls', 'r')
                dst_path = os.path.join(jail_dir, 'judge')
                with open(dst_path, 'w') as judge_dst:
                    shutil.copyfileobj(judge_src, judge_dst, judge_src.length)
                os.chmod(dst_path, stat.S_IREAD | stat.S_IEXEC)
                judge_src.close()
                jr = JailRun(submit=submit, root=jail_dir, path='/judge')
                jr.run()
            except:
                traceback.print_exc()
            finally:
                jb.destroy()
        else:
            time.sleep(sleep_time)

def judge_initialize():
    if False:
        subprocess.check_call(['busybox', 'mdev', '-s'])
        subprocess.check_call(['mkdir', '-p', '/dev/pts'])
        subprocess.check_call(['mount', '-t', 'devpts', '-o', 'rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000', 'devpts', '/dev/pts'])
        subprocess.check_call(['ln', '-s', '/proc/self/fd/0', '/dev/stdin'])
        subprocess.check_call(['ln', '-s', '/proc/self/fd/1', '/dev/stdout'])
        subprocess.check_call(['ln', '-s', '/proc/self/fd/2', '/dev/stderr'])
        subprocess.check_call(['/usr/sbin/sshd'])

    subprocess.check_call(['iptables', '-F', 'INPUT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'INVALID', '-j', 'DROP'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'eth+', '-p', 'tcp', '--dport', '22', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-i', 'veth+', '-p', 'tcp', '--dport', '8765', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'INPUT', '-j', 'LOG'])
    subprocess.check_call(['iptables', '-P', 'INPUT', 'ACCEPT'])

    subprocess.check_call(['iptables', '-F', 'OUTPUT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'INVALID', '-j', 'DROP'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'owner', '--uid-owner', 'root', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-m', 'owner', '--uid-owner', 'daemon', '-j', 'ACCEPT'])
    subprocess.check_call(['iptables', '-A', 'OUTPUT', '-j', 'LOG'])
    subprocess.check_call(['iptables', '-P', 'OUTPUT', 'ACCEPT'])

    subprocess.check_call(['iptables', '-F', 'FORWARD'])
    subprocess.check_call(['iptables', '-P', 'FORWARD', 'ACCEPT'])

    subprocess.check_call(['mkdir', '-p', cgroup_dir])
    subprocess.check_call(['mount', '-t', 'cgroup', '-o', 'rw,nosuid,noexec,relatime,memory,cpuacct,cpuset', 'cgroup', cgroup_dir])
    subprocess.check_call(['mkdir', '-p', templates_dir])
    subprocess.check_call(['mount', templates_src, templates_dir])

def judge_finalize():
        subprocess.call(['umount', '-l', cgroup_dir])
        subprocess.call(['rmdir', cgroup_dir])
        subprocess.call(['umount', '-l', templates_dir])
        subprocess.call(['rmdir', templates_dir])
        #subprocess.call(['reboot', '-f'])

def judge_init():
    try:
        judge_initialize()
        judge_loop()
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

