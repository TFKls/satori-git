#!/bin/bash

for TYPE in generic server; do
    echo ${TYPE}
    VER=`ls system/lib/modules |grep "${TYPE}" |sort |tail -n 1`
    if [ -z "${VER}" ]; then
        continue
    fi
    echo "${VER}"
    rm -rf "${VER}"
    mkdir "${VER}"
    cp -a template/* template/.??* "${VER}"
    V=`ls "${VER}"/initrd/lib/modules |sort |tail -n 1`
    if [ "${V}" != "${VER}" ]; then
        mv "${VER}"/initrd/lib/modules/"${V}" "${VER}"/initrd/lib/modules/"${VER}"
    fi
    cp -a system/boot/vmlinuz-"${VER}" "${VER}"/vmlinuz
    chmod 644 "${VER}"/vmlinuz
    cp -a system/lib/firmware/"${VER}" "${VER}"/initrd/lib/firmware
    ./update-modules.pl "${VER}"/initrd/lib/modules/"${VER}" system/lib/modules/"${VER}"
    ./update-modules.pl "${VER}"/initrd/lib/firmware system/lib/firmware
    cd "${VER}"
    ./umount.sh
    cd ..
    tar -c -j -f "${VER}/modules.tar.bz2" -C "system/lib/modules/" "${VER}"
    rm current-${TYPE}
    ln -s "${VER}" current-${TYPE}
done
