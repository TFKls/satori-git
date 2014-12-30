#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=checker
BUILDDIR="build-${TAG}"

rm -rf "${BUILDDIR}"
mkdir -p "${BUILDDIR}"
add_header "${BUILDDIR}" "${DOCKER_REPO}:judge"
add_apt_cacher "${BUILDDIR}"

cat >> "${BUILDDIR}/Dockerfile" <<EOF
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get --no-install-recommends -f -y install ${CHECKER_PACKAGES}
RUN hg clone https://bitbucket.org/satoriproject/satori /root/satori
RUN /root/satori/install_judge.sh
RUN rm -rf /root/satori

RUN rm -rf /root/tcs-scripts
ADD tcs-scripts /root/tcs-scripts
RUN /root/tcs-scripts/tcs-nvidia
RUN /root/tcs-scripts/tcs-cuda
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
