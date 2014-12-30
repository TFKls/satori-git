#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=judge
BUILDDIR="build-${TAG}"

rm -rf "${BUILDDIR}"
mkdir -p "${BUILDDIR}"
add_header "${BUILDDIR}" "${DOCKER_REPO}:base"
add_apt_cacher "${BUILDDIR}"

cat >> "${BUILDDIR}/Dockerfile" <<EOF
RUN apt-add-repository "ppa:satoriproject/satori"
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get --no-install-recommends -f -y install ${JUDGE_PACKAGES}
RUN apt-get install libssh2-1

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
#    unshare -m docker -- build "$@" "--tag=${DOCKER_REPO}:${TAG}raw" "${BUILDDIR}"
    docker export "${DOCKER_REPO}:${TAG}raw" | docker import - "${DOCKER_REPO}:${TAG}"
#    docker rmi "${DOCKER_REPO}:${TAG}raw"
fi

popd
