#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
ARCH=amd64
OTHER_ARCHITECTURES="i386"
DISTRO=trusty
LOCALE=en_US.UTF-8
APTCACHER="http://149.156.75.213:3142"
KEYSERVER="keyserver.ubuntu.com"
MAINTAINER="Grzegorz Gutowski <gutowski@tcs.uj.edu.pl>"
DOCKER_REPO="satoriproject/satori"

BASE_DIR="${OFFICE}/${DISTRO}_${ARCH}_base"
BASE_PACKAGES="locales software-properties-common"

JUDGE_PACKAGES="satori-testing gcc g++ gcc-multilib g++-multilib fp-compiler openjdk-7-jdk a2ps iptables time make p7zip-full p7zip-rar python-yaml libstdc++6:i386 libgcc1:i386 zlib1g:i386 libncurses5:i386"
CHECKER_PACKAGES="${JUDGE_PACKAGES} linux-image-generic linux-headers-generic linux-tools-generic smartmontools mdadm lvm2 ssh nfs-client nbd-client vim screen mc rsync gpm bash-completion psmisc mercurial debootstrap squashfs-tools tshark nmap ethtool iptraf ctorrent atftp lzma lshw memtest86+ strace telnet usbutils command-not-found language-pack-en network-manager subversion unzip mercurial reptyr dnsutils docker.io vlan"
UZI_PACKAGES="${JUDGE_PACKAGES} linux-image-generic linux-headers-generic linux-tools-generic openssh-server rsync gpm ubuntu-desktop indicator-applet-complete indicator-session indicator-datetime unity-lens-applications unity-lens-files xserver-xorg-video-all command-not-found language-pack-en gnome-terminal google-chrome-stable vim vim-gnome cscope emacs xemacs21 geany geany-plugins codeblocks scite xterm mc gedit gdb ddd xwpe nemiver stl-manual gcc-doc fp-docs manpages-dev manpages-posix manpages-posix-dev nano valgrind bash-completion ubiquity user-setup libgd2-xpm-dev dconf-tools openjdk-7-doc network-manager eclipse eclipse-cdt ctorrent screen konsole kate ethtool python-tk python3-tk reptyr dnsutils gnome-session-fallback compiz-plugins"
EXTENDED_PACKAGES="${CHECKER_PACKAGES} ${UZI_PACKAGES} gccgo gccgo-multilib golang-go golang-go.tools postgresql ant ant-contrib mlton flex gprolog mono-gmcs mono-runtime ghc nasm bison python python3 python-dev python3-dev sqlite3 libcgal-dev libgmp-dev"
LIGHT_PACKAGES="${JUDGE_PACKAGES} linux-image-generic openssh-server rsync gpm xserver-xorg xserver-xorg-video-all lxdm lubuntu-default-session lightdm command-not-found language-pack-en vim vim-gnome cscope emacs xemacs21 geany geany-plugins mc gedit gdb ddd xwpe nemiver manpages-dev manpages-posix manpages-posix-dev nano valgrind bash-completion ubiquity user-setup dconf-tools ctorrent screen ethtool python-tk reptyr dnsutils x2goclient google-chrome-stable"
FULL_PACKAGES="${CHECKER_PACKAGES} ${UZI_PACKAGES} dmraid rdate casper libstdc++5 clang google-perftools libgoogle-perftools-dev gprolog"
FULL_PACKAGES="${FULL_PACKAGES} firefox icedtea-7-plugin icedtea-netx netbeans eclipse eclipse-cdt maven2 x2goclient x2goserver"
FULL_PACKAGES="${FULL_PACKAGES} gnome-desktop-environment gnome-shell gnome-applets gnome-backgrounds gnome-control-center gnome-do gnome-system-tools gnome-themes-ubuntu gnome-video-effects"
FULL_PACKAGES="${FULL_PACKAGES} compiz-plugins compizconfig-settings-manager"
FULL_PACKAGES="${FULL_PACKAGES} ftp meld kwrite kdbg kate konsole"
FULL_PACKAGES="${FULL_PACKAGES} sssd ldap-utils ldap-auth-client libpam-cracklib libpam-pwquality libpam-sss libpam-afs-session krb5-user libpam-mount libpam-ssh openafs-client openafs-krb5 rdiff-backup squashfs-tools sshfs exfat-fuse exfat-utils smbclient"
FULL_PACKAGES="${FULL_PACKAGES} aspell-en aspell-pl language-pack-pl language-pack-en language-pack-gnome-pl language-pack-gnome-en language-pack-kde-pl language-pack-kde-en myspell-en-us myspell-en-gb myspell-pl"
FULL_PACKAGES="${FULL_PACKAGES} bash-completion openvpn finger"
FULL_PACKAGES="${FULL_PACKAGES} libtool autotools-dev autoconf binutils-dev automake bison cmake dpatch ddd flex indent m4 monodevelop mono-mcs mono-gmcs nasm ocaml cervisia codelite doxygen intltool intltool-debian ipython libboost-dev php5-cli rails rhino jedit"
FULL_PACKAGES="${FULL_PACKAGES} postgresql-client pgadmin3 sqlite3 python-virtualenv python-scipy"
FULL_PACKAGES="${FULL_PACKAGES} alien dpkg-dev arj debootstrap bc bcrypt mcrypt cabextract zip unzip rar unrar ctorrent lzip lzma make nfs-client nbd-client smartmontools mdadm lvm2 lsof p7zip-full pwgen zoo unace unshield"
FULL_PACKAGES="${FULL_PACKAGES} lynx elinks alpine wget mutt w3m procmail ncftp hexedit curl"
FULL_PACKAGES="${FULL_PACKAGES} blender gimp inkscape dia djview gnuplot"
FULL_PACKAGES="${FULL_PACKAGES} opera google-chrome-stable google-talkplugin thunderbird konqueror calibre"
FULL_PACKAGES="${FULL_PACKAGES} libreoffice-base"
FULL_PACKAGES="${FULL_PACKAGES} nodejs-legacy npm"
FULL_PACKAGES="${FULL_PACKAGES} coq erlang gap ghc gfortran agda smlnj rlwrap"
FULL_PACKAGES="${FULL_PACKAGES} dosbox dosemu tofrodos"
FULL_PACKAGES="${FULL_PACKAGES} ethtool fakeroot iproute iptraf mtr nmap tshark htop iotop iftop mdbtools ltrace strace telnet tcpdump traceroute wireshark xosview"
FULL_PACKAGES="${FULL_PACKAGES} flashplugin-installer mplayer mencoder x264 smplayer vlc libav-tools"
FULL_PACKAGES="${FULL_PACKAGES} frozen-bubble"
FULL_PACKAGES="${FULL_PACKAGES} kadu kdesvn konwert krusader kile digikam dolphin pidgin kfind"
FULL_PACKAGES="${FULL_PACKAGES} latex2html texlive-full latexdraw latex2rtf html2text html2ps pdfjam texmaker texpower pdftk ipe"
FULL_PACKAGES="${FULL_PACKAGES} cups-pdf exif expect gnome-genius gnokii gnome-commander clipit screenlets"
FULL_PACKAGES="${FULL_PACKAGES} xfig xnest xpdf xvfb xvnc4viewer geeqie imagemagick"
FULL_PACKAGES="${FULL_PACKAGES} gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly"
FULL_PACKAGES="${FULL_PACKAGES} scilab r-recommended"
FULL_PACKAGES="${FULL_PACKAGES} virtualbox virtualbox-guest-utils wine dropbox nautilus-open-terminal spotify-client"
FULL_PACKAGES="${FULL_PACKAGES} ttf-unifont msttcorefonts"
FULL_PACKAGES="${FULL_PACKAGES} subversion git mercurial libglew1.5 mysql-client ivy menu"
FULL_PACKAGES="${FULL_PACKAGES} orbit2 time gv openjpeg-tools"
FULL_PACKAGES="${FULL_PACKAGES} mlton shutter libboost-all-dev devscripts evtest mesa-utils ekg2 clusterssh tmux pipelight docker.io inotify-tools zlibc"
FULL_PACKAGES="${FULL_PACKAGES} libwxgtk2.8-dev libmysqlclient-dev libpq-dev python-dev python3-dev libgsl0-dev libqt4-dev tk-dev"
FULL_PACKAGES="${FULL_PACKAGES} ocrodjvu tesseract-ocr-pol"
FULL_PACKAGES="${FULL_PACKAGES} libgflags-dev enscript groovy scala rdesktop xubuntu-desktop" 

FULL_PACKAGES="${FULL_PACKAGES} linux-source vlan apt-cacher-ng nginx apache2-mpm-prefork libapache2-svn libapache2-mod-fcgid libfcgi-perl libfcgi-ruby1.8 libapache2-mod-proxy-html libapache2-mod-auth-mysql apache2-suexec-custom php5-cgi php5-curl php5-gd php5-mysql php5-pgsql bittorrent clamav clamav-daemon dovecot-imapd dovecot-pop3d exim4 exim4-daemon-heavy greylistd srs memcached memtest86+ memtester nfs-kernel-server nbd-server php5 quota quotatool spamassassin tinyca tinyproxy wakeonlan ntp atftpd subversion-tools mercurial-server trac trac-mercurial bittorrent trac-bitten ant maven2 ivy ant-contrib python-zc.buildout postgresql mysql-server ipmitool nut"
FULL_PACKAGES="${FULL_PACKAGES} libwxgtk2.8-dev libmysqlclient-dev libpq-dev python-dev libevent-dev libplot-dev libplplot-dev libzbar-dev libqrencode-dev libgsl0-dev libhighgui-dev libopenjpeg-dev libsfml-dev libcsfml-dev libfreeimage-dev libavdevice-dev libavfilter-dev libpostproc-dev libcgal-dev libtheora-dev libopencv-dev libclang-dev cabal-install mpich2"
FULL_PACKAGES="${FULL_PACKAGES} ruby-dev libruby libfcgi-dev fcgiwrap"
FULL_PACKAGES="${FULL_PACKAGES} python-django python-flup python-psycopg2 python-mysqldb ubuntu-desktop kubuntu-desktop xubuntu-desktop qt-sdk"
FULL_PACKAGES="${FULL_PACKAGES} bogofilter dhcp3-server bridge-utils erlang glassfish-javaee glassfish-appserv tomcat7 tomcat7-user nut-monitor r-recommended scilab vsftpd"

function uniq_pack_list
{
    echo "$@" |tr " " "\n" |sort |uniq |tr "\n" " "
}
JUDGE_PACKAGES=`uniq_pack_list $JUDGE_PACKAGES`
CHECKER_PACKAGES=`uniq_pack_list $CHECKER_PACKAGES`
UZI_PACKAGES=`uniq_pack_list $UZI_PACKAGES`
LIGHT_PACKAGES=`uniq_pack_list $LIGHT_PACKAGES`
EXTENDED_PACKAGES=`uniq_pack_list $EXTENDED_PACKAGES`
FULL_PACKAGES=`uniq_pack_list $FULL_PACKAGES`


unset DEBCONF_REDIR
unset DEBIAN_HAS_FRONTEND
export DEBIAN_PRIORITY=critical
export DEBIAN_FRONTEND=noninteractive

unset LANGUAGE
unset LC_CTYPE
unset LC_NUMERIC
unset LC_TIME
unset LC_COLLATE
unset LC_MONETARY
unset LC_MESSAGES
unset LC_PAPER
unset LC_NAME
unset LC_ADDRESS
unset LC_TELEPHONE
unset LC_MEASUREMENT
unset LC_IDENTIFICATION
export LANG="${LOCALE}"
export LC_ALL="${LOCALE}"

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

function add_apt_cacher
{
    BUILDDIR="$1"
    if [ -n "${APTCACHER}" ]; then
        cat >> "${BUILDDIR}/Dockerfile" <<EOF
RUN echo "Acquire::http::Proxy \"${APTCACHER}\";" > /etc/apt/apt.conf.d/90apt-cacher
EOF
    fi
}
function rem_apt_cacher
{
    BUILDDIR="$1"
    if [ -n "${APTCACHER}" ]; then
        cat >> "${BUILDDIR}/Dockerfile" <<EOF
RUN rm -f /etc/apt/apt.conf.d/90apt-cacher
EOF
    fi
}
function copy_scripts
{
    TAG="$1"
    BUILDDIR="$2"
    cp -a tcs-scripts "${BUILDDIR}"
    cp -a settings.sh "${BUILDDIR}/tcs-scripts"
    if [ -d "tcs-debs-${TAG}" ]; then
        cp -a "tcs-debs-${TAG}" "${BUILDDIR}"/tcs-scripts/debs
    fi
    if [ "$3" == "kernel" ]; then
        cp -a tcs-kernel "${BUILDDIR}"/tcs-scripts/kernel 
    fi
}
function add_header
{
    BUILDDIR="$1"
    BASE="$2"
    cat > "${BUILDDIR}/Dockerfile" <<EOF
FROM ${BASE}
MAINTAINER ${MAINTAINER}

ENV DEBIAN_PRIORITY critical
ENV DEBIAN_FRONTEND noninteractive
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

EOF
}
function add_footer
{
    BUILDDIR="$1"
    cat >> "${BUILDDIR}/Dockerfile" <<EOF
EOF
}
