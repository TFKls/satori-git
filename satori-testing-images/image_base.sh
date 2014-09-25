#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=base

rm -rf "${TAG}"
mkdir -p "${TAG}"
add_header "${TAG}" "ubuntu:${DISTRO}"
add_apt_cacher "${TAG}"

cat >> "${TAG}/Dockerfile" <<EOF
RUN locale-gen en_US.UTF-8
RUN echo rm -f /etc/apt/sources.list.d/*
RUN echo "deb     http://archive.ubuntu.com/ubuntu ${DISTRO} main restricted universe multiverse" > /etc/apt/sources.list 
RUN echo "deb-src http://archive.ubuntu.com/ubuntu ${DISTRO} main restricted universe multiverse" >> /etc/apt/sources.list 
RUN echo "deb     http://archive.ubuntu.com/ubuntu ${DISTRO}-updates main restricted universe multiverse" >> /etc/apt/sources.list
RUN echo "deb-src http://archive.ubuntu.com/ubuntu ${DISTRO}-updates main restricted universe multiverse" >> /etc/apt/sources.list
RUN echo "deb     http://archive.ubuntu.com/ubuntu ${DISTRO}-security main restricted universe multiverse" >> /etc/apt/sources.list
RUN echo "deb-src http://archive.ubuntu.com/ubuntu ${DISTRO}-security main restricted universe multiverse" >> /etc/apt/sources.list
RUN dpkg --add-architecture i386
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get -f -y install software-properties-common python
ADD tcs-scripts /root/tcs-scripts
RUN /root/tcs-scripts/tcs-scripts
RUN rm -rf /root/tcs-scripts
RUN apt-get -y autoremove
RUN apt-get -y clean
EOF

rem_apt_cacher "${TAG}"
add_footer "${TAG}"

copy_scripts "${TAG}"

if [ "$1" != "debug" ]; then
    docker build "--tag=${DOCKER_REPO}:${TAG}" "${TAG}"
fi

popd
