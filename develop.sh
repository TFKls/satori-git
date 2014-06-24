#!/bin/bash
OFFICE=$(dirname $(readlink -f $(which $0)))
pushd "$OFFICE"
unset PYTHONPATH
if [ ! -e bin/activate ]; then
  ./bootstrap.sh
fi
source bin/activate || exit 1

( cd thrift/lib/py  && python2 setup.py install )
( cd thrift/lib/py3 && python3 setup.py install )

for i in $(cat PYTHON_PACKAGE_LIST) ; do 
    pushd "$i" || exit 1; python2 setup.py develop; python3 setup.py develop; popd
done

popd
