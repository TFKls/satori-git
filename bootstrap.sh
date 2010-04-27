#!/bin/bash

#
#  bootstrap.sh -- build environment bootstrap
#
#  run this script _once_ after checking out the sources
#  to prepare your work environment
#

virtualenv-2.6 --no-site-packages .
source bin/activate
easy_install zc.buildout
mkdir -p src/python var/{buildout,cache}
buildout
