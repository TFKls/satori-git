#!/bin/bash

cd "$(dirname "$(readlink -f "$0")")"
aptitude -y install python-virtualenv python-dev libpq-dev libyaml-dev libcap-dev make patch
unset PYTHONPATH
virtualenv --no-site-packages .
source bin/activate
easy_install -U distribute
