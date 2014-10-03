#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=server


rm -rf "${TAG}"
mkdir -p "${TAG}"
add_header "${TAG}" "${DOCKER_REPO}:full"
add_apt_cacher "${TAG}"

cat >> "${TAG}/Dockerfile" <<EOF
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get -d -f -y install ${SERVER_PACKAGES}
RUN apt-get -f -y install ${SERVER_PACKAGES}
RUN apt-get -f -y install nvidia-cuda-toolkit nvidia-304 linux-headers-generic

ADD tcs-scripts /root/tcs-scripts
RUN /root/tcs-scripts/tcs-scripts
RUN rm -rf /root/tcs-scripts
RUN apt-get -y autoremove
RUN apt-get -y clean
EOF

rem_apt_cacher "${TAG}"
add_footer "${TAG}"

copy_scripts "${TAG}" kernel

if [ "$1" != "debug" ]; then
    docker build "--tag=${DOCKER_REPO}:${TAG}" "${TAG}"

    rm -rf kernel
    mkdir -p kernel
    ./docker_image_extract "${DOCKER_REPO}:${TAG}" kernel /root/vmlinuz /root/initrd.cpio.lzma /root/modules.tar.bz2
fi

popd
