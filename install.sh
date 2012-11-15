#!/bin/bash
OFFICE=$(dirname $(readlink -f $(which $0)))
pushd "$OFFICE"
unset PYTHONPATH
if [ ! -e bin/activate ]; then
  ./bootstrap.sh
fi
source bin/activate || exit 1

for i in $(cat PYTHON_PACKAGE_LIST) ; do 
    pushd "$i" || exit 1; python setup.py install; popd
done

popd
