#!/bin/bash

if [ -r .mounted ]; then
  echo "initrd mounted... exiting"
  exit 1
fi

mkdir initrd &&
cd initrd &&
gzip -d -c ../initrd.cpio.gz | cpio -i --no-absolute-filenames &&
cd .. &&
touch .mounted