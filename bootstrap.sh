#!/bin/bash

#
#  bootstrap.sh -- build environment bootstrap
#
#  run this script _once_ after checking out the sources
#  to prepare your work environment
#

aptitude install python-virtualenv python-dev libpq-dev libyaml-dev libcap-dev
unset PYTHONPATH
virtualenv --no-site-packages .
ln -s python bin/python2.6
source bin/activate
easy_install zc.buildout
easy_install -U distribute
mkdir -p src/python var/{buildout,cache}
buildout
