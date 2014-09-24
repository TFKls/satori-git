#!/bin/bash

RD="initrd"
SYS="../system"
DESTDIR="$RD"

if [ ! -r .mounted ]; then
  echo "initrd not mounted... exiting"
  exit 1
fi

. /usr/share/initramfs-tools/hook-functions


for i in busybox dropbear dbclient atftp cp rsync ctorrent readlink tar vim.basic nbd-client; do
    rm -f "$RD/bin/$i"
    rm -f "$RD/sbin/$i"

    for s in "$SYS/usr/bin/$i" "$SYS/bin/$i"; do
        if [ -e "$s" ]; then
            copy_exec "$s" "/bin"
            break
        fi
    done

    for s in "$SYS/usr/sbin/$i" "$SYS/sbin/$i"; do
        if [ -e "$s" ]; then
            copy_exec "$s" "/sbin"
            break
        fi
    done
    if [ ! -x "$RD/bin/$i" -a ! -x "$RD/sbin/$i" ]; then
        echo "$i not found!"
    fi
done
mv "$RD/bin/vim.basic" "$RD/bin/vim"
ln -s "dbclient" "$RD/bin/ssh"

pushd "$RD/bin"
./busybox --help |grep -A 100 "Currently defined functions" |grep "," |tr -d "\n" |sed -e "s|\s||g" |tr "," "\n" |while read b; do
    if [ ! -e "$b" ]; then
        ln -s busybox "$b"
    fi
done
popd

mkdir -p "$RD/home/root"
