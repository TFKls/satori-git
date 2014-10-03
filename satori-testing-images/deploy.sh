#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

function get
{
    src="${DISTRO}_amd64_debooted_${1}.squashfs"
    if [ ! -e "$src" ]; then
        ./docker_image_squash "${DOCKER_REPO}:$2" "$src"
    fi
}

function deploy
{
    src="${DISTRO}_amd64_debooted_${1}.squashfs"
    if [ -e "$src" ]; then
        chmod 644 "$src"
        screen -dmS `echo "$2" | md5sum /dev/fd/0 |sed -e "s|\(.\{5\}\).*|\1|"` rsync -a -P -p "$src" "$2"
        rm "$2.torrent" >/dev/null 2>&1
    else
        echo "File $src does not exist"
    fi
}

function deployk
{
    chmod 644 kernel/{vmlinuz,initrd.cpio.lzma}
    rsync -a -P -p kernel/{vmlinuz,initrd.cpio.lzma} "$1"
}

get judge judge
exit 0
get checker checker
get uzi uzi
get full full
get server full


deploy judge   /exports/checker/judge.squashfs
deploy server  /exports/checker/full.squashfs

deploy checker /exports/booter/booter.cfg/__BASE__/CHECKER/filesystem.squashfs
deploy uzi    /exports/booter/booter.cfg/__BASE__/UZI/filesystem.squashfs
deploy full   /exports/booter/booter.cfg/__BASE__/DESKTOP/filesystem.squashfs
deploy server /exports/booter/booter.cfg/__BASE__/SERVER/filesystem.squashfs
#deploy server root@sphinx:/exports/booter/booter.cfg/__BASE__/SERVER/filesystem.squashfs
deploy uzi    /exports/booter/casper.uzi/filesystem.squashfs
deployk /boot/casper
deployk root@sphinx.direct:/boot/casper
deployk root@student.direct:/boot/casper
deployk root@miracle.direct:/boot/casper
deployk /exports/booter/booter.cfg/__BASE__/KERNEL
deployk /srv/tftp/KERNEL
deployk /root/.VirtualBox/TFTP/KERNEL

deploy uzi    /imports/wydzial/casper.uzi/filesystem.squashfs
deployk /imports/wydzialtftp/uzi/KERNEL

deploy full   /imports/wydzial/__BASE__/DESKTOP/filesystem.squashfs
deployk /imports/wydzialtftp/pracownicy
deployk /imports/wydzialtftp/studenci
