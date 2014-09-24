#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=judge

rm -rf ".${TAG}"
mkdir -p ".${TAG}"
cat > ".${TAG}/Dockerfile" <<EOF
FROM tcs:base
MAINTAINER ${MAINTAINER}

ENV DEBIAN_PRIORITY critical
ENV DEBIAN_FRONTEND noninteractive
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

RUN echo "Acquire::http::Proxy \"${APTCACHER}\";" > /etc/apt/apt.conf.d/90apt-cacher

RUN apt-get-keys
RUN apt-get --no-install-recommends -f -y install ${JUDGE_PACKAGES}

RUN apt-get autoremove
RUN apt-get clean

ADD tcs-scripts /root/tcs-scripts
RUN /root/tcs-scripts/tcs-scripts
RUN rm -rf /root/tcs-scripts

RUN rm -f /etc/apt/apt.conf.d/90apt-cacher
EOF

cp -a tcs-scripts ".${TAG}"
if [ -d "tcs-debs-${TAG}" ]; then
    cp -a "tcs-debs-${TAG}" ".${TAG}"/tcs-scripts/debs
fi

if [ "$1" != "debug" ]; then
    docker build "--tag=tcs:${TAG}" ".${TAG}"
fi

popd
