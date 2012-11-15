#!/bin/bash
OFFICE=$(dirname $(readlink -f $(which $0)))
VENV=".virtual_env"
pushd "$OFFICE"

apt-get -y install python-virtualenv python-dev libpopt-dev libcurl4-openssl-dev libpq-dev libyaml-dev libcap-dev make patch
unset PYTHONPATH

virtualenv --no-site-packages --prompt=\(satori\) "$VENV" &&
mkdir -p bin &&
ln -s "../$VENV"/bin/activate* bin/activate &&
source bin/activate &&
easy_install -U distribute || exit 1

popd
