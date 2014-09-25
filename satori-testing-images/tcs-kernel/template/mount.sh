#!/bin/bash

if [ -r .mounted ]; then
  echo "initrd mounted... exiting"
  exit 1
fi

mkdir initrd &&
cd initrd &&
lzma -d -c ../initrd.cpio.lzma | cpio -i --no-absolute-filenames &&
cd .. &&
touch .mounted
