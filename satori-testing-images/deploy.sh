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
    rsync -a -P -p kernel/vmlinuz "$1/$2"
    rsync -a -P -p kernel/initrd.cpio.lzma "$1/$2.cpio.lzma"
}

get judge judge
get checker checker
get uzi uzi
get light light
get extended extended
get full full
get desktop desktop
#exit 0


deploy judge    /exports/checker/judge.squashfs
deploy extended /exports/checker/full.squashfs

deploy checker  /exports/booter/booter.cfg/__BASE__/CHECKER/filesystem.squashfs
deploy full     /exports/booter/booter.cfg/__BASE__/FULL/filesystem.squashfs
deploy desktop  /exports/booter/booter.cfg/__BASE__/DESKTOP/filesystem.squashfs
deploy uzi      /exports/booter/casper.uzi/filesystem.squashfs
deploy light    /exports/booter/casper.test/filesystem.squashfs

deployk /srv/tftp/KERNEL tcs

deploy uzi      /imports/wydzial/casper.uzi/filesystem.squashfs
deployk         /imports/wydzialtftp/uzi/KERNEL tcs

#deploy desktop  /imports/wydzial/__BASE__/DESKTOP/filesystem.squashfs
#deployk         /imports/wydzialtftp/pracownicy tcs
#deployk         /imports/wydzialtftp/studenci tcs
