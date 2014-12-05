#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=full


rm -rf "${TAG}"
mkdir -p "${TAG}"
add_header "${TAG}" "${DOCKER_REPO}:judge"
add_apt_cacher "${TAG}"

cat >> "${TAG}/Dockerfile" <<EOF
RUN apt-add-repository ppa:x2go/stable
RUN apt-add-repository ppa:pipelight/stable
RUN echo "deb http://get.docker.io/ubuntu docker main" >> /etc/apt/sources.list 
RUN apt-key adv --keyserver "${KEYSERVER}" --recv-key D8576A8BA88D21E9
RUN echo "deb http://linux.dropbox.com/ubuntu ${DISTRO} main" >> /etc/apt/sources.list
RUN apt-key adv --keyserver "${KEYSERVER}" --recv-key FC918B335044912E
RUN echo "deb http://dl.google.com/linux/deb/ stable main" >> /etc/apt/sources.list
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list
RUN echo "deb http://dl.google.com/linux/talkplugin/deb/ stable main" >> /etc/apt/sources.list
RUN apt-key adv --keyserver "${KEYSERVER}" --recv-key A040830F7FAC5991
RUN echo "deb http://deb.opera.com/opera stable non-free" >> /etc/apt/sources.list
RUN apt-key adv --keyserver "${KEYSERVER}" --recv-key 517590D9A8492E35
RUN echo "deb http://repository.spotify.com stable non-free" >> /etc/apt/sources.list 
RUN apt-key adv --keyserver "${KEYSERVER}" --recv-key 082CCEDF94558F59

#  run_inside locale-gen "pl_PL.UTF-8"
#  echo acroread acroread/default-viewer select true | run_inside debconf-set-selections
#  echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | run_inside debconf-set-selections
 
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get -d -f -y install ${FULL_PACKAGES}
RUN apt-get -f -y install ${FULL_PACKAGES}
RUN apt-get -f -y install nvidia-cuda-toolkit nvidia-304 linux-headers-generic
RUN update-java-alternatives -s java-1.7.0-openjdk-amd64
RUN pipelight-plugin --update
RUN pipelight-plugin --disable-all
RUN pipelight-plugin --remove-mozilla-plugins

ADD tcs-scripts /root/tcs-scripts
RUN /root/tcs-scripts/tcs-avcodec
RUN /root/tcs-scripts/tcs-virtualbox
RUN /root/tcs-scripts/tcs-satoriclient
RUN /root/tcs-scripts/tcs-kernel
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
