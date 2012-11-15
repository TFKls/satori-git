#!/bin/bash
OFFICE=$(dirname $(readlink -f $(which $0)))
pushd "$OFFICE"

apt-get -y install python-virtualenv python-dev libpopt-dev libcurl4-openssl-dev libpq-dev libyaml-dev libcap-dev make patch
unset PYTHONPATH

virtualenv --no-site-packages . &&
source bin/activate &&
easy_install -U distribute || exit 1

popd
