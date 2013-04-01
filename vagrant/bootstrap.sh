#!/bin/sh

test -d /opt/satori/virtualenv || virtualenv --no-site-packages /opt/satori/virtual_env
. /opt/satori/virtual_env/bin/activate
easy_install -U distribute

cd /opt/satori/src
for i in $(cat PYTHON_PACKAGE_LIST) ; do
cd "/opt/satori/src/$i"; python setup.py develop
done

# Hack: treat .bash_aliases as a local .bashrc
cp /opt/satori/src/vagrant/bashrc ~/.bash_aliases

mkdir -p /opt/satori/run
