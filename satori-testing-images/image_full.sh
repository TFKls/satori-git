#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=full

rm -rf ".${TAG}"
mkdir -p ".${TAG}"
cat > ".${TAG}/Dockerfile" <<EOF
FROM tcs:judge
MAINTAINER ${MAINTAINER}

ENV DEBIAN_PRIORITY critical
ENV DEBIAN_FRONTEND noninteractive
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

RUN echo "Acquire::http::Proxy \"${APTCACHER}\";" > /etc/apt/apt.conf.d/90apt-cacher

RUN echo "deb http://ppa.launchpad.net/x2go/stable/ubuntu ${DISTRO} main" >> /etc/apt/sources.list
RUN echo "deb http://ppa.launchpad.net/pipelight/stable/ubuntu ${DISTRO} main" >> /etc/apt/sources.list
RUN echo "deb http://linux.dropbox.com/ubuntu ${DISTRO} main" >> /etc/apt/sources.list
RUN echo "deb http://dl.google.com/linux/deb/ stable main" >> /etc/apt/sources.list
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list
RUN echo "deb http://dl.google.com/linux/talkplugin/deb/ stable main" >> /etc/apt/sources.list
RUN echo "deb http://deb.opera.com/opera stable non-free" >> /etc/apt/sources.list
RUN echo "deb http://repository.spotify.com stable non-free" >> /etc/apt/sources.list 
RUN echo "deb http://get.docker.io/ubuntu docker main" >> /etc/apt/sources.list 
#  run_inside locale-gen "pl_PL.UTF-8"
#  echo acroread acroread/default-viewer select true | run_inside debconf-set-selections
#  echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | run_inside debconf-set-selections
 
RUN apt-get-keys
RUN apt-get -d -f -y install ${FULL_PACKAGES}
RUN apt-get -f -y install ${FULL_PACKAGES}
RUN apt-get -f -y install nvidia-cuda-toolkit nvidia-304 linux-headers-generic

ADD tcs-scripts /root/tcs-scripts

RUN update-java-alternatives -s java-1.7.0-openjdk-amd64
RUN /root/tcs-scripts/tcs-avcodec
RUN /root/tcs-scripts/tcs-virtualbox
RUN /root/tcs-scripts/tcs-satoriclient
RUN pipelight-plugin --update
RUN pipelight-plugin --disable-all
RUN pipelight-plugin --remove-mozilla-plugins

RUN /root/tcs-scripts/tcs-kernel

RUN apt-get autoremove
RUN apt-get clean

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

    rm -rf kernel
    mkdir -p kernel
    ./docker_image_extract "tcs:${TAG}" kernel /root/vmlinuz /root/initrd.cpio.lzma /root/modules.tar.bz2
fi

popd
