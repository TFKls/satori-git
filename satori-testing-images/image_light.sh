#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

TAG=light

rm -rf "${TAG}"
mkdir -p "${TAG}"
add_header "${TAG}" "${DOCKER_REPO}:judge"
add_apt_cacher "${TAG}"

REMOVE="firefox pidgin sylpheed transmission-gtk transmission-common transmission abiword abiword-common audacious guvcview gnome-mplayer xfburn gnumeric"
cat >> "${TAG}/Dockerfile" <<EOF
RUN apt-add-repository "deb http://dl.google.com/linux/deb/ stable main"
RUN apt-add-repository "deb http://dl.google.com/linux/chrome/deb/ stable main"
RUN apt-add-repository "deb http://dl.google.com/linux/talkplugin/deb/ stable main"
RUN apt-key adv --keyserver "${KEYSERVER}" --recv-key A040830F7FAC5991
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get -f -y install lubuntu-desktop
RUN apt-get -f -y install ${LIGHT_PACKAGES}
RUN apt-get -y remove ${REMOVE}
RUN apt-get -y purge ${REMOVE}
RUN apt-get -f -y install nvidia-304 linux-headers-generic
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
    docker build "$@" "--tag=${DOCKER_REPO}:${TAG}" "${TAG}"
fi

popd
