#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
VENV=".virtual_env"
pushd "$OFFICE"

apt-get -y install python-virtualenv python-dev libpopt-dev libcurl4-openssl-dev libpq-dev libyaml-dev libcap-dev make patch
unset PYTHONPATH

virtualenv --no-site-packages --prompt=\(satori\) "$VENV" &&
mkdir -p bin &&
find "$VENV/bin" -name "activate*" |while read a; do ln -s "../$a" bin; done &&
source bin/activate &&
pip install -U distribute || exit 1

popd
