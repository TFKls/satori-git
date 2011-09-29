#!/bin/bash

#
#  bootstrap.sh -- build environment bootstrap
#
#  run this script _once_ after checking out the sources
#  to prepare your work environment
#

cd "$(dirname "$(readlink -f "$0")")"
aptitude -y install python-virtualenv python-dev libpq-dev libyaml-dev libcap-dev make patch
unset PYTHONPATH
virtualenv --no-site-packages .
PVER=$(python --version 2>&1 |sed -e "s|^.*\\s\([0-9]\+\\.[0-9]\+\).*$|\1|")
ln -s python "bin/python${PVER}"
ln -s python "bin/python2.6"
source bin/activate
easy_install zc.buildout
rm local/lib/python*/site-packages/zc.buildout-*.egg/zc/buildout/easy_install.pyc
patch local/lib/python*/site-packages/zc.buildout-*.egg/zc/buildout/easy_install.py <<EOF
--- easy_install.py     2011-09-29 15:05:18.802287546 +0000
+++ easy_install.py2    2011-09-29 15:22:54.182076890 +0000
@@ -175,20 +175,13 @@
     try:
         return _versions[executable]
     except KeyError:
-        cmd = _safe_arg(executable) + ' -V'
-        p = subprocess.Popen(cmd,
-                             shell=True,
-                             stdin=subprocess.PIPE,
-                             stdout=subprocess.PIPE,
-                             stderr=subprocess.STDOUT,
-                             close_fds=not is_win32)
-        i, o = (p.stdin, p.stdout)
-        i.close()
-        version = o.read().strip()
-        o.close()
-        pystring, version = version.split()
-        assert pystring == 'Python'
-        version = re.match('(\d[.]\d)([.].*\d)?$', version).group(1)
+        stdout, stderr = subprocess.Popen(
+            [executable, '-Sc',
+             'import sys\n'
+             'print \'%d.%d\' % sys.version_info[:2]\n'
+            ],
+        stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
+        version=stdout.strip()
         _versions[executable] = version
         return version
 
EOF
easy_install -U distribute
mkdir -p src/python var/{buildout,cache}
buildout -c buildout_judge.cfg
(
  cd satori.judge/runner
  make runner
  cp runner /usr/bin
)
