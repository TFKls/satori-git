#!/bin/bash

#
#  bootstrap.sh -- build environment bootstrap
#
#  run this script _once_ after checking out the sources
#  to prepare your work environment
#

cd "$(dirname "$(readlink -f "$0")")"
aptitude -y install python-virtualenv python-dev libpq-dev libyaml-dev libcap-dev make
unset PYTHONPATH
virtualenv --no-site-packages .
PVER=$(python --version 2>&1 |sed -e "s|^.*\\s\([0-9]\+\\.[0-9]\+\).*$|\1|")
ln -s python "bin/python${PVER}"
source bin/activate
easy_install zc.buildout
easy_install -U distribute
mkdir -p src/python var/{buildout,cache}
buildout
