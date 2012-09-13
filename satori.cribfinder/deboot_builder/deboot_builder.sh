#!/bin/bash
# vim:ts=2:sts=2:sw=2:expandtab
unset DEBCONF_REDIR
unset DEBIAN_HAS_FRONTEND
export DEBIAN_PRIORITY=critical
export DEBIAN_FRONTEND=noninteractive

unset LANG
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
unset LC_ALL

debootstrap=`which debootstrap`
runner=`which runner`
mksquashfs=`which mksquashfs`
if [ -z "${debootstrap}" -o -z "${runner}" -o -z "${mksquashfs}" ]; then
    echo "need to install debootstrap and runner and squashfs-tools"
    exit 1
fi

MYSELF=`which $0`
MYSELF=`readlink -f "${MYSELF}"`
MYDIR=`dirname "${MYSELF}"`
MYCODE=`md5sum "${MYSELF}" |cut -d " " -f 1`

if [ -z "${ARCH}" ]; then
  ARCH=amd64
fi
if [ -z "${DIST}" ]; then
  DIST=oneiric
fi
INC=aptitude,locales
LOC=en_US.UTF-8
JUDGE="gcc g++ gcc-4.4 g++-4.4 fp-compiler openjdk-6-jdk a2ps iptables python-yaml libpopt-dev libcap-dev libcurl4-openssl-dev libyaml-dev time libgmp3-dev make"
CHECKER="${JUDGE} linux-image-server linux-headers-server smartmontools mdadm lvm2 ssh nfs-client vim screen mc rsync bash-completion psmisc mercurial debootstrap squashfs-tools tshark nmap ethtool iptraf ctorrent atftp lzma lshw memtest86+ strace telnet usbutils command-not-found language-pack-en"
UZI="${JUDGE} linux-server linux-headers-server nscd dkms openssh-server rsync xubuntu-desktop xorg xserver-xorg-video-vesa lzma lshw memtest86+ strace telnet usbutils xserver-xorg-video-all command-not-found language-pack-en firefox icedtea-plugin vim emacs geany geany-plugins mc gedit kate konsole gdb nemiver stl-manual gcc-doc fp-docs manpages-dev manpages-posix manpages-posix-dev nano valgrind bash-completion ubiquity user-setup libgd2-xpm libsdl1.2debian-pulseaudio dconf-tools openjdk-6-doc acroread"
DEBIAN="${UZI} linux-image-amd64 vim gnome"
FULL="${CHECKER} ${UZI} dmraid rdate casper libstdc++5"
FULL="${FULL} eclipse eclipse-jdt ftp meld kwrite kdbg"
FULL="${FULL} nscd ldap-utils ldap-auth-client libnss-ldap libpam-afs-session libpam-krb5 krb5-user libpam-ldap libpam-mount libpam-ssh openafs-client openafs-krb5 rdiff-backup squashfs-tools sshfs smbfs"
FULL="${FULL} aspell-en aspell-pl language-pack-pl language-pack-en language-pack-gnome-pl language-pack-gnome-en language-pack-kde-pl language-pack-kde-en myspell-en-us myspell-en-gb myspell-pl"
FULL="${FULL} bash-completion openvpn finger"
FULL="${FULL} libtool autotools-dev autoconf binutils-dev automake bison cmake dpatch ddd flex indent m4 monodevelop nasm ocaml cervisia codelite doxygen intltool intltool-debian ipython libboost-dev php5-cli rails rhino jedit"
FULL="${FULL} postgresql-client sqlite3 python-virtualenv python-scipy"
FULL="${FULL} avant-window-navigator"
FULL="${FULL} alien dpkg-dev arj debootstrap bc bcrypt mcrypt cabextract zip unzip rar unrar ctorrent lzip lzma make nfs-client smartmontools mdadm lvm2 lsof p7zip-full pwgen zoo lha unace unshield"
FULL="${FULL} lynx elinks alpine wget mutt w3m procmail ncftp hexedit curl"
FULL="${FULL} blender gimp inkscape dia djview gnuplot qcad"
FULL="${FULL} opera google-chrome-stable google-talkplugin thunderbird konqueror"
FULL="${FULL} openoffice.org-base"
FULL="${FULL} coq erlang gap ghc6 gfortran"
FULL="${FULL} dosbox dosemu tofrodos"
FULL="${FULL} ethtool fakeroot ia32-libs iproute iptraf mtr nmap tshark htop ltrace strace telnet tcpdump traceroute wireshark xosview"
FULL="${FULL} ffmpeg flashplugin-installer mplayer mencoder w64codecs x264 smplayer vlc"
FULL="${FULL} frozen-bubble gnome-games"
FULL="${FULL} kadu kdesvn konwert krusader kile digikam dolphin pidgin kfind"
FULL="${FULL} latex2html texlive-full latexdraw latex2rtf html2text html2ps pdfjam texmaker texpower"
FULL="${FULL} cups-pdf exif expect gnome-genius gnokii gnome-commander parcellite screenlets"
FULL="${FULL} xfig xnest xpdf xvfb xvnc4viewer geeqie imagemagick"
FULL="${FULL} gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly"
FULL="${FULL} scilab r-recommended"
FULL="${FULL} skype virtualbox virtualbox-guest-additions virtualbox-guest-utils wine nautilus-dropbox nautilus-open-terminal lastfm"
FULL="${FULL} ttf-unifont msttcorefonts"
FULL="${FULL} git mercurial libglew1.5 mysql-client ivy menu"
FULL="${FULL} orbit2 time gv openjpeg-tools"
SERVER="${FULL} linux-server linux-headers-server linux-source vlan apt-cacher-ng apache2-mpm-prefork libapache2-mod-fcgid libapache2-mod-proxy-html libapache2-mod-auth-mysql apache2-suexec-custom php5-cgi php5-curl php5-gd php5-mysql php5-pgsql bittorrent clamav exim4 exim4-daemon-heavy greylistd srs memcached memtest86+ memtester nfs-kernel-server php5 quota quotatool spamassassin tinyca tinyproxy wakeonlan ntp atftpd subversion-tools mercurial-server trac trac-mercurial bittorrent trac-bitten ant maven2 ivy ant-contrib python-zc.buildout postgresql mysql-server"
SERVER="${SERVER} neatx-server libwxgtk2.8-dev libmysqlclient-dev libpq-dev python-dev libevent-dev libplot-dev libplplot-dev libzbar-dev libqrencode-dev libgsl0-dev libhighgui-dev libopenjpeg-dev libsfml-dev libcsfml-dev libfreeimage-dev"
SERVER="${SERVER} ruby-dev libruby libfcgi-dev fcgiwrap"
SERVER="${SERVER} python-django python-psycopg2 python-mysqldb ubuntu-desktop kubuntu-desktop xubuntu-desktop"
DIR="${MYDIR}/${DIST}_${ARCH}_debooted"
TMP="${MYDIR}/.${DIST}_${ARCH}.tmp"
APTCACHER="http://149.156.75.213:3142"
KEYSERVER="keyserver.ubuntu.com"
FORBID="apparmor global postfix"


SOURCES="${DIR}"/etc/apt/sources.list
APTCACHER_CONF=/etc/apt/apt.conf.d/90apt-cacher
CONFFILES="/etc/resolv.conf /etc/hostname /etc/timezone ${APTCACHER_CONF}"
UPSTARTFILES="/sbin/init /sbin/initctl /sbin/reboot /sbin/runlevel /sbin/shutdown /sbin/telinit /sbin/upstart-udev-bridge /sbin/start /sbin/stop /sbin/restart /sbin/reload /sbin/status /sbin/halt /sbin/poweroff"

RI_PAR_ETH="vethdbp"
RI_PAR_IP="10.211.33.113"
RI_NETMASK="255.255.255.0"
RI_CHI_ETH="vethdbc"
RI_CHI_IP="10.211.33.114"

function uniq_pack_list
{
    echo "$@" |tr " " "\n" |sort |uniq
}
JUDGE=`uniq_pack_list $JUDGE`
CHECKER=`uniq_pack_list $CHECKER`
UZI=`uniq_pack_list $UZI`
DEBIAN=`uniq_pack_list $DEBIAN`
FULL=`uniq_pack_list $FULL`
SERVER=`uniq_pack_list $SERVER`

function run_inside_child
{
  tmp_dir="$1"
  shift
  echo -n "$$" > "${tmp_dir}/pid"
  while [ ! -f "${tmp_dir}/go" ]; do sleep 1; done
  ifconfig lo 127.0.0.1 netmask 255.0.0.0 up
  ifconfig "${RI_CHI_ETH}" "${RI_CHI_IP}" netmask "${RI_NETMASK}" up
  route add default gw "${RI_PAR_IP}"
  echo runner --silent --root="${DIR}" --pivot --work-dir=/root --ns-ipc --ns-mount --ns-pid --mount-proc --ns-uts --env-add=LANG="${LOC}" --search "$@"
  runner --silent --root="${DIR}" --pivot --work-dir=/root --ns-ipc --ns-mount --ns-pid --mount-proc --ns-uts --env-add=LANG="${LOC}" --search "$@"
  echo -n "$?" > "${tmp_dir}/result"
}
if [ "$1" == "run_inside_child" ]; then
  shift
  run_inside_child "$@"
  exit 0
fi

function run_inside
{
  disable_init
  ip link del "${RI_PAR_ETH}" > /dev/null 2>&1
  ip link add name "${RI_PAR_ETH}" type veth peer name "${RI_CHI_ETH}"
  ifconfig "${RI_PAR_ETH}" "${RI_PAR_IP}" netmask "${RI_NETMASK}" up
  tmp_dir="${TMP}/RI"
  rm -rf "${tmp_dir}"
  mkdir -p "${tmp_dir}"
  chmod 700 "${tmp_dir}"
  runner --quiet --ns-net "${MYSELF}" run_inside_child "${tmp_dir}" "$@" < /dev/stdin > /dev/stdout 2> /dev/stderr &
  while [ ! -f "${tmp_dir}/pid" ]; do sleep 1; done
  pid=`cat "${tmp_dir}/pid"`
  ip link set "${RI_CHI_ETH}" netns "${pid}"
  ip_forward=`cat /proc/sys/net/ipv4/ip_forward`
  echo 1 > /proc/sys/net/ipv4/ip_forward
  iptables -t nat -I POSTROUTING -s "${RI_CHI_IP}" -j MASQUERADE
  touch "${tmp_dir}/go"
  wait
  while [ ! -f "${tmp_dir}/result" ]; do sleep 1; done
  result=`cat "${tmp_dir}/result"`
  iptables -t nat -D POSTROUTING -s "${RI_CHI_IP}" -j MASQUERADE
  ip link del "${RI_PAR_ETH}" > /dev/null 2>&1
  echo "${ip_forward}" > /proc/sys/net/ipv4/ip_forward
  rm -rf "${tmp_dir}"
  restore_init
  return $result
}

function finalize
{
  umount -l "${DIR}"/{proc,sys,dev}
  umount -l "${DIR}"
  rm -rf "${TMP}"
  return 0
}

function initialize
{
  rm -rf "${TMP}"
  mkdir "${TMP}"
  mkdir "${DIR}"
  mount -o bind "${DIR}" "${DIR}" &&
  return 0
  finalize
  return 1
}

function store
{
  FILE="$1"
  F="${DIR}${FILE}"
  B=`basename "${FILE}"`
  B="${TMP}/${B}"
  mv "${F}" "${B}"
  return 0
}

function restore
{
  FILE="$1"
  F="${DIR}${FILE}"
  B=`basename "${FILE}"`
  B="${TMP}/${B}"
  mv "${B}" "${F}"
  return 0
}

function inject
{
  FILE="$1"
  cp "${FILE}" "${DIR}${FILE}"
  return 0
}

function store_conf
{
  for i in ${CONFFILES}; do
    store "${i}"
  done
  return 0
}

function restore_conf
{
  for i in ${CONFFILES}; do
    restore "${i}"
  done
  return 0
}

function inject_conf
{
  for i in ${CONFFILES}; do
    inject "${i}"
  done
  return 0
}

function disable_init
{
  for i in ${UPSTARTFILES}; do
    store "${i}"
    echo "#!/bin/bash" >"${DIR}${i}"
    echo "exit 0" >"${DIR}${i}"
    chmod 755 "${DIR}${i}"
  done
}

function restore_init
{
  for i in ${UPSTARTFILES}; do
    restore "${i}"
  done
}

function initialize_full
{
  rm -rf "${TMP}"
  mkdir "${TMP}"
  mkdir "${DIR}"
  mkdir "${DIR}"/proc
  mkdir "${DIR}"/dev
  mount -o bind "${DIR}" "${DIR}" &&
  mount -o rbind "/proc" "${DIR}"/proc &&
  mount -o rbind "/dev" "${DIR}"/dev &&
  mount -o rbind "/sys" "${DIR}"/sys &&
  inject_conf &&
  return 0
  finalize
  return 1
}

function make_squash
{
  RES="$1"
  run_inside aptitude -y clean
  for l in `find "${DIR}"/var/log -type f`; do
    :> "$l"
  done
  for f in `find "${DIR}"/root "${DIR}"/tmp "${DIR}"/var/crash -mindepth 1`; do
    rm -rf "$f"
  done


  umount -l "${DIR}"/{proc,sys,dev}
  umount -l "${DIR}"
  store_conf
  ./remap.py "${DIR}"
  rm -f "${RES}"
  OK=0
  mksquashfs "${DIR}" "${RES}" -noappend &&
  chmod 644 "${RES}" &&
  OK=1
  restore_conf
  initialize_full

  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function use_squash
{
  SRC="$1"
  store /etc/resolv.conf
  store /etc/hostname
  store "${APTCACHER_CONF}"
  finalize
  rm -rf "${DIR}"
  OK=0
  unsquashfs -dest "${DIR}" "${SRC}" &&
  OK=1
  restore /etc/resolv.conf
  restore /etc/hostname
  restore "${APTCACHER_CONF}"

  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function vbox_add
{
  return 0
  OK=0
  mkdir -p "${TMP}"/VBoxGuestAdditions &&
  mount -o loop "${DIR}"/usr/share/virtualbox/VBoxGuestAdditions.iso "${TMP}"/VBoxGuestAdditions &&
  cp -a "${TMP}"/VBoxGuestAdditions/VBoxLinuxAdditions-amd64.run "${DIR}"/root/VBoxLinuxAdditions-amd64.run &&
  run_inside ./VBoxLinuxAdditions-amd64.run &&
  run_inside /etc/init.d/vboxdrv setup
  OK=1
  umount -l "${TMP}"/VBoxGuestAdditions
  rm -rf "${TMP}"/VBoxGuestAdditions "${DIR}"/root/VBoxLinuxAdditions-amd64.run

  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function dkms_all
{
  for KER in `ls "${DIR}"/lib/modules |sort`; do
  ls "${DIR}"/usr/src |sed -e "s|\(.*\)-\(.*\)|\1 \2|" |while read line; do
    MOD=`echo "$line" |cut -d " " -f 1`
    VER=`echo "$line" |cut -d " " -f 2`
    CHK=`echo "${MOD}" |cut -d "-" -f 1`
    if [ "$CHK" == "linux" ]; then
      continue
    fi
    echo "${MOD}" "${VER}" "${KER}"
    run_inside dkms add -m "${MOD}" -v "${VER}"
    run_inside dkms build -m "${MOD}" -v "${VER}" -k "${KER}"
    run_inside dkms install -m "${MOD}" -v "${VER}" -k "${KER}"
  done
  done
}

function avcodec_extra
{
    list=`run_inside aptitude search "^lib[asp][vwo].*-extra-[0-9]" |cut -d " " -f 4 |grep "^lib" |xargs echo`
    run_inside apt-get -y install $list
}

function cuda_toolkit
{
  cp -a cuda/NVIDIA-Linux*.run "${DIR}"/root/nvidiadriver.run &&
  chmod 755 "${DIR}"/root/nvidiadriver.run &&
  cp -a cuda/cudatoolkit*.run "${DIR}"/root/cudatoolkit.run &&
  chmod 755 "${DIR}"/root/cudatoolkit.run &&
  cp -a cuda/cudatools*.run "${DIR}"/root/cudatools.run &&
  chmod 755 "${DIR}"/root/cudatools.run &&
  cp -a cuda/gpucomputingsdk*.run "${DIR}"/root/gpusdk.run &&
  chmod 755 "${DIR}"/root/gpusdk.run

  run_inside apt-get -y install make perl-modules linux-headers-server
  for TYPE in server; do
    echo ${TYPE}
    VER=`ls "${DIR}"/lib/modules |grep "${TYPE}" |sort |tail -n 1`
    if [ -z "${VER}" ]; then
        continue
    fi
    run_inside /root/nvidiadriver.run --no-distro-scripts --no-cc-version-check --no-x-check --no-nouveau-check --no-network --no-runlevel-check --accept-license --no-backup --no-precompiled-interface --ui=none --no-questions -k "${VER}"
  done
  mkdir -p "${DIR}"/usr/local/cuda
  run_inside /root/cudatoolkit.run -- --prefix=/usr/local/cuda
  run_inside /root/cudatools.run --
  run_inside /root/gpusdk.run -- --prefix=/usr/local/cuda/NVIDIA_GPU_Computing_SDK
  mkdir -p /usr/local/cuda/cc
  ln -s /usr/bin/g++-4.4 /usr/local/cuda/cc
  ln -s /usr/bin/gcc-4.4 /usr/local/cuda/cc
  echo 'compiler-bindir  = $(TOP)/cc' >> /usr/local/cuda/nvcc.profile
  cat > "${DIR}"/usr/local/bin/nvcc <<EOF
  #!/bin/bash
  exec /usr/local/cuda/bin/nvcc "$@"
EOF
  chmod 755 "${DIR}"/usr/local/bin/nvcc
  $( cd "${DIR}"/usr/local/bin
  for i in ../cuda/bin/* ../cuda/open64/bin/* ../cuda/computeprof/bin/computeprof; do
    if [ -x "$i" ]; then
      ln -s "$i" "${DIR}"/usr/local/bin
    fi
  done
  ln -s ../cuda/include "${DIR}"/usr/local/include/cuda
  ln -s ../cuda/lib64/* "${DIR}"/usr/local/lib )
  rm "${DIR}"/root/{nvidiadriver,cudatoolkit,cudatools,gpusdk}.run
}

function build_base
{
  OK=0
  finalize
  rm -rf "${DIR}"
  apt_cache="${APTCACHER}/archive.ubuntu.com/ubuntu"
  if [ "${DIST}" == "squeeze" ]; then
    apt_cache="${APTCACHER}/ftp.debian.org/debian"
  fi
  initialize &&
  debootstrap --arch="${ARCH}" --include "${INC}" "${DIST}" "${DIR}" "${apt_cache}" &&
  OK=1
  if [ "${OK}" == "1" ]; then
    OK=0
    make_squash "${DIR}"_base.squashfs &&
    OK=1
  fi

  finalize
  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function build_judge
{
  OK=0
  ( [ -f "${DIR}"_base.squashfs ] || build_base ) &&
  use_squash "${DIR}"_base.squashfs &&
  initialize_full &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST} main restricted universe multiverse" > "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-updates main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://security.ubuntu.com/ubuntu ${DIST}-security main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-backports main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.canonical.com/ ${DIST} partner" >> "${SOURCES}" &&
  echo "Acquire::http::Proxy \"${APTCACHER}\";" > "${DIR}${APTCACHER_CONF}" &&
  run_inside locale-gen "${LOC}" &&
  echo sun-java6-jre shared/accepted-sun-dlj-v1-1 select true | run_inside debconf-set-selections &&
  echo sun-java6-jdk shared/accepted-sun-dlj-v1-1 select true | run_inside debconf-set-selections &&
  run_inside aptitude -y update &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  run_inside apt-get --no-install-recommends -y install ${JUDGE} &&
  OK=1

  if [ "${OK}" == "1" ]; then
    OK=0
    make_squash "${DIR}"_judge.squashfs &&
    OK=1
  fi

  finalize
  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function build_debian
{
  OK=0
  use_squash "${DIR}"_base.squashfs &&
  initialize_full &&
  echo "deb http://ftp.debian.org/debian/ ${DIST} main non-free contrib" > "${SOURCES}" &&
  echo "deb http://security.debian.org/ ${DIST}/updates main non-free contrib" >> "${SOURCES}" &&
  echo "deb http://ftp.debian.org/debian/ ${DIST}-updates main non-free contrib" >> "${SOURCES}" &&
  echo "deb http://backports.debian.org/debian-backports ${DIST}-backports main non-free contrib" >> "${SOURCES}" &&
  echo "deb http://www.debian-multimedia.org ${DIST} main non-free" >> "${SOURCES}" &&
  echo "deb http://live.debian.net/ ${DIST}-snapshots main contrib non-free" >> "${SOURCES}" &&
  echo "deb http://download.virtualbox.org/virtualbox/debian ${DIST} non-free contrib" >> "${SOURCES}" &&
  echo "deb http://deb.opera.com/opera stable non-free" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/talkplugin/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://linux.dropbox.com/debian ${DIST} main" >> "${SOURCES}" &&
  echo "deb http://apt.last.fm/ debian stable" >> "${SOURCES}" &&
  echo "Acquire::http::Proxy \"${APTCACHER}\";" > "${DIR}${APTCACHER_CONF}" &&
  run_inside locale-gen "${LOC}" &&
  echo sun-java6-jre shared/accepted-sun-dlj-v1-1 select true | run_inside debconf-set-selections &&
  echo sun-java6-jdk shared/accepted-sun-dlj-v1-1 select true | run_inside debconf-set-selections &&
  echo acroread acroread/default-viewer select true | run_inside debconf-set-selections &&
  find_missing_keys &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  (
  run_inside apt-get -y install ${DEBIAN}
  run_inside aptitude -y purge ${FORBID}
  run_inside apt-get --no-install-recommends -y install ${DEBIAN}
  exit $?
  ) &&
  OK=1
  if [ "${OK}" == "1" ]; then
    OK=0
    make_squash "${DIR}"_debian.squashfs &&
    OK=1
  fi
  finalize
  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function find_missing_keys
{
  run_inside aptitude -y update
  find "${DIR}"/var/lib/apt/ -name "*.gpg" | while read l; do
    key=`gpg --verify "$l" "$l" 2>&1 |head -n 1|sed -e "s|.* ||"`
    echo "${key}"
  done |sort |uniq |while read key; do
    run_inside apt-key adv --keyserver "${KEYSERVER}" --recv-key "${key}"
    gpg --ignore-time-conflict --no-options --no-default-keyring --secret-keyring /etc/apt/secring.gpg --trustdb-name /etc/apt/trustdb.gpg --keyring /etc/apt/trusted.gpg --primary-keyring /etc/apt/trusted.gpg --armor --export "${key}" |run_inside apt-key add -
  done
  run_inside aptitude -y update
  return 0
}

function build_checker
{
  OK=0
  ( [ -f "${DIR}"_judge.squashfs ] || build_judge ) &&
  use_squash "${DIR}"_judge.squashfs &&
  initialize_full &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  run_inside apt-get --no-install-recommends -y install ${CHECKER} &&
  cuda_toolkit &&
  hg clone --insecure "https://develro:XVxPqc99Rnsf@satori.tcs.uj.edu.pl/hg/satori" "${DIR}"/opt/satori &&
  run_inside /opt/satori/bootstrap_judge.sh &&
  OK=1

  if [ "${OK}" == "1" ]; then
    OK=0
    make_squash "${DIR}"_checker.squashfs &&
    OK=1
  fi

  finalize
  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function build_uzi
{
  OK=0
  ( [ -f "${DIR}"_judge.squashfs ] || build_judge ) &&
  ( [ -f "${DIR}"_checker.squashfs ] || build_checker ) &&
  use_squash "${DIR}"_judge.squashfs &&
  initialize_full &&
  echo acroread acroread/default-viewer select true | run_inside debconf-set-selections &&
  find_missing_keys &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  (
  run_inside apt-get -y install ${UZI}
  run_inside aptitude -y purge ${FORBID}
  run_inside apt-get --no-install-recommends -y install ${UZI}
  exit $?
  ) &&
  cuda_toolkit &&
  dkms_all &&
  OK=1

  if [ "${OK}" == "1" ]; then
    OK=0
    make_squash "${DIR}"_uzi.squashfs &&
    OK=1
  fi

  finalize
  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function build_full
{
  OK=0
  ( [ -f "${DIR}"_uzi.squashfs ] || build_uzi ) &&
  use_squash "${DIR}"_uzi.squashfs &&
  initialize_full &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST} main restricted universe multiverse" > "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-updates main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://security.ubuntu.com/ubuntu ${DIST}-security main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-backports main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.canonical.com/ ${DIST} partner" >> "${SOURCES}" &&
  echo "deb http://packages.medibuntu.org/ ${DIST} free non-free" >> "${SOURCES}" &&
  echo "deb http://ppa.launchpad.net/freenx-team/ppa/ubuntu lucid main" >> "${SOURCES}" &&
  echo "deb http://download.virtualbox.org/virtualbox/debian ${DIST} non-free contrib" >> "${SOURCES}" &&
  echo "deb http://deb.opera.com/opera stable non-free" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/talkplugin/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://linux.dropbox.com/ubuntu ${DIST} main" >> "${SOURCES}" &&
  echo "deb http://linux.dropbox.com/ubuntu natty main" >> "${SOURCES}" &&
  echo "deb http://apt.last.fm/ debian stable" >> "${SOURCES}" &&
  echo "Acquire::http::Proxy \"${APTCACHER}\";" > "${DIR}${APTCACHER_CONF}" &&
  find_missing_keys &&
  run_inside locale-gen "pl_PL.UTF-8" &&
  echo acroread acroread/default-viewer select true | run_inside debconf-set-selections &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  (
    run_inside apt-get -y install ${FULL}
    for package in ${FULL}; do
      run_inside apt-get -y install ${package}
    done
    run_inside aptitude -y purge ${FORBID}
    run_inside apt-get --no-install-recommends -y install ${FULL}
    exit $?
  ) &&
  run_inside update-java-alternatives -s openjdk-6 &&
  cp -a debs "${DIR}"/root &&
  (
    R=0
    for i in debs/*.deb; do
      run_inside dpkg -i /root/"${i}" || R=1
    done
    exit ${R}
  ) &&
  avcodec_extra &&
  dkms_all &&
  vbox_add &&
  cuda_toolkit &&
  OK=1

  if [ "${OK}" == "1" ]; then
    OK=0
    make_squash "${DIR}"_full.squashfs &&
    OK=1
  fi

  finalize
  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}

function build_server
{
  OK=0
  ( [ -f "${DIR}"_full.squashfs ] || build_full ) &&
  use_squash "${DIR}"_full.squashfs &&
  initialize_full &&
  echo "deb-src http://archive.ubuntu.com/ubuntu ${DIST} main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb-src http://archive.ubuntu.com/ubuntu ${DIST}-updates main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb-src http://security.ubuntu.com/ubuntu ${DIST}-security main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb-src http://archive.ubuntu.com/ubuntu ${DIST}-backports main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb-src http://archive.canonical.com/ ${DIST} partner" >> "${SOURCES}" &&
  echo "deb-src http://packages.medibuntu.org/ ${DIST} free non-free" >> "${SOURCES}" &&
  echo "deb-src http://ppa.launchpad.net/freenx-team/ppa/ubuntu lucid main" >> "${SOURCES}" &&
  find_missing_keys &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  (
    run_inside apt-get -y install ${SERVER}
    for package in ${SERVER}; do
      run_inside apt-get -y install ${package}
    done
    run_inside aptitude -y purge ${FORBID}
    run_inside apt-get --no-install-recommends -y install ${SERVER}
    for i in ${SERVER}; do
      run_inside apt-get -y build-dep ${i}
    done
    run_inside aptitude -y purge winbind network-manager network-manager-gnome network-manager-pptp network-manager-pptp-gnome
    for service in atftpd lightdm gdm kdm exim4 apt-cacher-ng memcached inetd tinyproxy ntp mysql postgres postgresql; do
      run_inside update-rc.d -f $service remove
      run_inside mv /etc/init/$service.conf /etc/init/$service.conf.DISABLED
    done
    exit 0
  ) &&
  cp -a debs_server "${DIR}"/root &&
  (
    R=0
    for i in debs_server/*.deb; do
      run_inside dpkg -i /root/"${i}" || R=1
    done
    exit ${R}
  ) &&
  dkms_all &&
  vbox_add &&
  OK=1

  if [ "${OK}" == "1" ]; then
    OK=0
    make_squash "${DIR}"_server.squashfs &&
    OK=1
  fi

  finalize
  if [ "${OK}" == "1" ]; then
    return 0
  fi
  return 1
}


if [ "$1" == "squash" ]; then
  initialize_full &&
  make_squash "${DIR}"_squash.squashfs
  finalize
  exit 0
fi

if [ "$1" == "dkms" ]; then
  initialize_full &&
  dkms_all &&
  vbox_add
  finalize
  exit 0
fi

if [ "$1" == "bash" ]; then
  initialize_full &&
  run_inside bash
  finalize
  exit 0
fi

if [ "$1" == "call" ]; then
  shift
  initialize_full &&
  run_inside "$@"
  finalize
  exit 0
fi


if [ "$1" == "base" ]; then
    build_base
    exit 0
fi

if [ "$1" == "judge" ]; then
    build_judge
    exit 0
fi

if [ "$1" == "checker" ]; then
    build_checker
    exit 0
fi

if [ "$1" == "debian" ]; then
    build_debian
    exit 0
fi

if [ "$1" == "uzi" ]; then
    build_uzi
    exit 0
fi

if [ "$1" == "full" ]; then
    build_full
    exit 0
fi

if [ "$1" == "server" ]; then
    build_server
    exit 0
fi

if [ "$1" == "clean" ]; then
    rm -f "${DIR}"_base.squashfs "${DIR}"_judge.squashfs "${DIR}"_checker.squashfs "${DIR}"_uzi.squashfs "${DIR}"_full.squashfs "${DIR}"_server.squashfs
    exit 0
fi

if [ "$1" == "cuda" ]; then
    initialize_full &&
    avcodec_extra
    finalize
    exit 0
fi


echo " --- ### $0 ### --- "
echo " Usage: "
echo " $0 squash | dkms | bash | call | base | judge | checker | debian | uzi | full | server | clean"
exit 1
