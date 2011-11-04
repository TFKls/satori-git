#!/bin/bash

for i in $(cat PYTHON_PACKAGE_LIST) ; do 
    (cd $i ; python setup.py develop )
done
