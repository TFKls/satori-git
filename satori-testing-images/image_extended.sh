#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=extended
BUILDDIR="build-${TAG}"

rm -rf "${BUILDDIR}"
mkdir -p "${BUILDDIR}"
add_header "${BUILDDIR}" "${DOCKER_REPO}:judge"
add_apt_cacher "${BUILDDIR}"

cat >> "${BUILDDIR}/Dockerfile" <<EOF
RUN apt-add-repository "deb http://dl.google.com/linux/deb/ stable main"
RUN apt-add-repository "deb http://dl.google.com/linux/chrome/deb/ stable main"
RUN apt-add-repository "deb http://dl.google.com/linux/talkplugin/deb/ stable main"
RUN apt-key adv --keyserver "${KEYSERVER}" --recv-key A040830F7FAC5991
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get -d -f -y install ${EXTENDED_PACKAGES}
RUN apt-get -f -y install ${EXTENDED_PACKAGES}
RUN update-java-alternatives -s java-1.7.0-openjdk-amd64

RUN rm -rf /root/tcs-scripts
ADD tcs-scripts /root/tcs-scripts
RUN /root/tcs-scripts/tcs-nvidia
RUN /root/tcs-scripts/tcs-cuda
RUN /root/tcs-scripts/tcs-kernel
RUN /root/tcs-scripts/tcs-scripts
RUN rm -rf /root/tcs-scripts
RUN apt-get -y autoremove
RUN apt-get -y clean
EOF

rem_apt_cacher "${BUILDDIR}"
add_footer "${BUILDDIR}"

copy_scripts "${TAG}" "${BUILDDIR}" kernel

if [ "$1" != "debug" ]; then
    unshare -m docker -- build "$@" "--tag=${DOCKER_REPO}:${TAG}" "${BUILDDIR}"

    rm -rf kernel
    mkdir -p kernel
    ./docker_image_extract "${DOCKER_REPO}:${TAG}" kernel /root/vmlinuz /root/initrd.cpio.lzma /root/modules.tar.bz2
fi

popd
