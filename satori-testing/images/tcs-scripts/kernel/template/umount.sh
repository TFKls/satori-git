#!/bin/bash

if [ ! -r .mounted ]; then
  echo "initrd not mounted... exiting"
  exit 1
fi

cd initrd &&
find . | cpio -o -H newc --reset-access-time > ../initrd.cpio &&
lzma ../initrd.cpio &&
cd .. &&
rm -rf initrd &&
rm .mounted

chmod 644 initrd.cpio.lzma
