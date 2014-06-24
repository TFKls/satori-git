#!/bin/bash
if which apt-get >/dev/null 2>&1; then
    apt-get -y install python-virtualenv python-dev libpopt-dev libcurl4-openssl-dev libpq-dev libyaml-dev libcap-dev make patch
fi

(
    cd $(dirname "$(readlink -f "$(which "$0")")")

    VENV=".virtual_env"
    unset PYTHONPATH

    for py in python2 python3; do
        if which $py >/dev/null 2>&1; then
            virtualenv --python=`which $py` --no-site-packages --prompt="(satori) " "$VENV"
        fi
    done

    ( mkdir -p bin && cd bin && cp -sf ../"$VENV"/bin/activate* . )
    source bin/activate
)
