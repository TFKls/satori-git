#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=base
BUILDDIR="build-${TAG}"

rm -rf "${BUILDDIR}"
mkdir -p "${BUILDDIR}"
add_header "${BUILDDIR}" "ubuntu:${DISTRO}"
add_apt_cacher "${BUILDDIR}"

cat >> "${BUILDDIR}/Dockerfile" <<EOF
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8
RUN rm -f /etc/apt/sources.list.d/*
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

RUN rm -rf /root/tcs-scripts
ADD tcs-scripts /root/tcs-scripts
RUN /root/tcs-scripts/tcs-scripts
RUN rm -rf /root/tcs-scripts
RUN apt-get -y autoremove
RUN apt-get -y clean
EOF

rem_apt_cacher "${BUILDDIR}"
add_footer "${BUILDDIR}"

copy_scripts "${TAG}" "${BUILDDIR}"

if [ "$1" != "debug" ]; then
    unshare -m docker -- build "$@" "--tag=${DOCKER_REPO}:${TAG}" "${BUILDDIR}"
fi

popd
