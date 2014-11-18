#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

find -name "${DISTRO}_amd64_debooted_*.squashfs" -exec rm {} \;

for dock_ps in $(docker ps -q -a); do
    docker rm ${dock_ps};
done
for dock_im in $(docker images | grep "^<none>" | awk "{print \$3}"); do
    docker rmi -f ${dock_im};
done

/root/bin/docker_cleanup

IMAGES="base judge extended checker uzi light full"

for image in ${IMAGES}; do
    docker rmi "${DOCKER_REPO}:${image}"
done
docker rmi "ubuntu:${DISTRO}"

./image_base.sh --no-cache &&
./image_judge.sh --no-cache &&
./image_checker.sh --no-cache &&
./image_uzi.sh --no-cache &&
./image_light.sh --no-cache &&
./image_extended.sh --no-cache &&
./image_full.sh --no-cache
