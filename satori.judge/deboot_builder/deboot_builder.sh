#!/bin/bash
#vim:ts=2:sts=2:sw=2:expandtab
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
  DIST=precise
fi
INC=aptitude,locales
LOC=en_US.UTF-8
JUDGE="gcc g++ gcc-4.4 g++-4.4 g++-4.7 gcc-4.7 fp-compiler openjdk-7-jdk a2ps iptables python-yaml libpopt-dev libcap-dev libcurl4-openssl-dev libyaml-dev time libgmp3-dev make"
CHECKER="${JUDGE} linux-image-generic linux-headers-generic smartmontools mdadm lvm2 ssh nfs-client vim screen mc rsync bash-completion psmisc mercurial debootstrap squashfs-tools tshark nmap ethtool iptraf ctorrent atftp lzma lshw memtest86+ strace telnet usbutils command-not-found language-pack-en network-manager subversion unzip mercurial"
UZI="${JUDGE} linux-image-generic openssh-server rsync ubuntu-desktop indicator-applet-complete indicator-session indicator-datetime-gtk2 unity-lens-applications unity-lens-files xserver-xorg-video-all command-not-found language-pack-en gnome-terminal google-chrome-stable vim vim-gnome cscope emacs xemacs21 geany geany-plugins mc gedit gdb ddd xwpe nemiver stl-manual gcc-doc fp-docs manpages-dev manpages-posix manpages-posix-dev nano valgrind bash-completion ubiquity user-setup libgd2-xpm dconf-tools openjdk-7-doc network-manager eclipse eclipse-cdt ctorrent screen konsole kate"
OLIMP="gcc g++ fp-compiler a2ps iptables time make linux-image-generic-pae linux-headers-generic-pae nfs-client vim screen mc rsync bash-completion ctorrent strace command-not-found language-pack-pl network-manager linux-image-generic-pae openssh-server rsync xubuntu-desktop xserver-xorg-video-all command-not-found language-pack-pl gnome-terminal google-chrome-stable vim vim-gnome cscope emacs xemacs21 geany geany-plugins mc gedit gdb ddd xwpe nemiver stl-manual gcc-doc fp-docs manpages-dev manpages-posix manpages-posix-dev nano valgrind bash-completion ubiquity user-setup libgd2-xpm dconf-tools openjdk-7-doc network-manager eclipse eclipse-cdt ctorrent screen konsole kate mc vim kate kwrite gedit gvim emacs scite codeblocks geany lazarus-ide gdb ddd valgrind gprof python gcalctool"
FULL="${CHECKER} ${UZI} dmraid rdate casper libstdc++5 jenkins clang google-perftools libgoogle-perftools-dev"
FULL="${FULL} firefox icedtea-7-plugin eclipse eclipse-cdt acroread maven2"
FULL="${FULL} gnome-desktop-environment gnome-shell gnome-applets gnome-backgrounds gnome-control-center gnome-do gnome-games gnome-system-tools gnome-themes-ubuntu gnome-utils gnome-video-effects"
FULL="${FULL} ftp meld kwrite kdbg kate konsole"
FULL="${FULL} nscd ldap-utils ldap-auth-client libnss-ldapd libpam-afs-session libpam-krb5 krb5-user libpam-ldap libpam-mount openafs-client openafs-krb5 rdiff-backup squashfs-tools sshfs smbfs fuse-exfat"
FULL="${FULL} aspell-en aspell-pl language-pack-pl language-pack-en language-pack-gnome-pl language-pack-gnome-en language-pack-kde-pl language-pack-kde-en myspell-en-us myspell-en-gb myspell-pl"
FULL="${FULL} bash-completion openvpn finger"
FULL="${FULL} libtool autotools-dev autoconf binutils-dev automake bison cmake dpatch ddd flex indent m4 monodevelop mono-mcs mono-gmcs nasm ocaml cervisia codelite doxygen intltool intltool-debian ipython libboost-dev php5-cli rails rhino jedit"
FULL="${FULL} postgresql-client pgadmin3 sqlite3 python-virtualenv python-scipy"
FULL="${FULL} avant-window-navigator"
FULL="${FULL} alien dpkg-dev arj debootstrap bc bcrypt mcrypt cabextract zip unzip rar unrar ctorrent lzip lzma make nfs-client smartmontools mdadm lvm2 lsof p7zip-full pwgen zoo lha unace unshield"
FULL="${FULL} lynx elinks alpine wget mutt w3m procmail ncftp hexedit curl"
FULL="${FULL} blender gimp inkscape dia djview gnuplot qcad"
FULL="${FULL} opera google-chrome-stable google-talkplugin thunderbird konqueror calibre"
FULL="${FULL} openoffice.org-base"
FULL="${FULL} coq erlang gap ghc6 gfortran"
FULL="${FULL} dosbox dosemu tofrodos"
FULL="${FULL} ethtool fakeroot ia32-libs iproute iptraf mtr nmap tshark htop ltrace strace telnet tcpdump traceroute wireshark xosview"
FULL="${FULL} ffmpeg flashplugin-installer mplayer mencoder w64codecs x264 smplayer vlc"
FULL="${FULL} frozen-bubble gnome-games"
FULL="${FULL} kadu kdesvn konwert krusader kile digikam dolphin pidgin kfind"
FULL="${FULL} latex2html texlive-full latexdraw latex2rtf html2text html2ps pdfjam texmaker texpower pdftk"
FULL="${FULL} cups-pdf exif expect gnome-genius gnokii gnome-commander clipit screenlets"
FULL="${FULL} xfig xnest xpdf xvfb xvnc4viewer geeqie imagemagick"
FULL="${FULL} gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly"
FULL="${FULL} scilab r-recommended"
FULL="${FULL} skype virtualbox virtualbox-guest-additions virtualbox-guest-utils wine dropbox nautilus-open-terminal lastfm spotify"
FULL="${FULL} ttf-unifont msttcorefonts"
FULL="${FULL} subversion git mercurial libglew1.5 mysql-client ivy menu"
FULL="${FULL} orbit2 time gv openjpeg-tools"
FULL="${FULL} mlton shutter libboost-all-dev devscripts evtest mesa-utils ekg2 clusterssh tmux caffeine"
FULL="${FULL} spotify-client"
SERVER="${FULL} linux-source vlan apt-cacher-ng nginx apache2-mpm-prefork libapache2-svn libapache2-mod-fcgid libfcgi-perl libfcgi-ruby1.8 libapache2-mod-proxy-html libapache2-mod-auth-mysql apache2-suexec-custom php5-cgi php5-curl php5-gd php5-mysql php5-pgsql bittorrent clamav clamav-daemon exim4 exim4-daemon-heavy greylistd srs memcached memtest86+ memtester nfs-kernel-server php5 quota quotatool spamassassin tinyca tinyproxy wakeonlan ntp atftpd subversion-tools mercurial-server trac trac-mercurial bittorrent trac-bitten ant maven2 ivy ant-contrib python-zc.buildout postgresql mysql-server"
SERVER="${SERVER} libwxgtk2.8-dev libmysqlclient-dev libpq-dev python-dev libevent-dev libplot-dev libplplot-dev libzbar-dev libqrencode-dev libgsl0-dev libhighgui-dev libopenjpeg-dev libsfml-dev libcsfml-dev libfreeimage-dev libavdevice-dev libavfilter-dev libpostproc-dev libcgal-dev libtheora-dev"
SERVER="${SERVER} ruby-dev libruby libfcgi-dev fcgiwrap"
SERVER="${SERVER} python-django python-psycopg2 python-mysqldb ubuntu-desktop kubuntu-desktop xubuntu-desktop qt-sdk"
DIR="${MYDIR}/${DIST}_${ARCH}_debooted"
TMP="${MYDIR}/.${DIST}_${ARCH}.tmp"
ABORT="${MYDIR}/.abort"
APTCACHER="http://149.156.75.213:3142"
KEYSERVER="keyserver.ubuntu.com"
FORBID="apparmor"


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
OLIMP=`uniq_pack_list $OLIMP`
FULL=`uniq_pack_list $FULL`
SERVER=`uniq_pack_list $SERVER`

function finalize
{
  umount -l "${DIR}"/{proc,sys,dev}
  umount -l "${DIR}"
  rm -rf "${TMP}"
  return 0
}

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
  if [ -f "${ABORT}" ]; then
    echo "File '${ABORT}' exists. Aborting. "
    finalize
    exit 1
  fi
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
  rm -f "${F}"
  mv "${B}" "${F}"
  return 0
}

function store_md5
{
  FILE="$1"
  F="${DIR}${FILE}"
  B=`basename "${FILE}"`
  B="${TMP}/${B}.md5"
  cat "${F}" |md5sum > "${B}"
  return 0
}

function check_md5
{
  FILE="$1"
  F="${DIR}${FILE}"
  B=`basename "${FILE}"`
  B="${TMP}/${B}.md5"
  n=`cat "${F}" |md5sum`
  t=`cat "${B}"`
  if [ "$n" == "$t" ]; then
    return 0
  fi
  return 1
}

function inject
{
  FILE="$1"
  cp "${FILE}" "${DIR}${FILE}"
  return 0
}

function store_conf
{
  for cf in ${CONFFILES}; do
    store "${cf}"
  done
  return 0
}

function restore_conf
{
  for cf in ${CONFFILES}; do
    restore "${cf}"
  done
  return 0
}

function inject_conf
{
  for cf in ${CONFFILES}; do
    inject "${cf}"
  done
  return 0
}

function disable_init
{
  for usf in ${UPSTARTFILES}; do
    store "${usf}"
    echo "#!/bin/bash" >"${DIR}${usf}"
    echo "exit 0" >>"${DIR}${usf}"
    chmod 755 "${DIR}${usf}"
    store_md5 "${usf}"
  done
}

function restore_init
{
  for usf in ${UPSTARTFILES}; do
    if check_md5 "${usf}"; then
      restore "${usf}"
    fi
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
  rm -rf "${DIR}"/etc/apt/sources.list.d/*
  run_inside apt-get -y clean
  for lf in `find "${DIR}"/var/log -type f`; do
    :> "$lf"
  done
  run_inside find /root /tmp /var/tmp /var/crash -mindepth 1 -exec rm -rf {} \; -prune
  run_inside find -L /run /var /tmp \( -type f -o -type s \) \( -name "*.pid" -o -name "*.sock" -o -name "lock" -o -name "*.lock" \) -exec rm -f {} \; -prune

  mkdir "${DIR}"/tmp/.X11-unix
  chmod 777 "${DIR}"/tmp/.X11-unix
  chmod o+t "${DIR}"/tmp/.X11-unix


  umount -l "${DIR}"/{proc,sys,dev}
  umount -l "${DIR}"
  store_conf
  if [ -e ./remap.py ]; then
    ./remap.py "${DIR}" || return 1
  fi
  rm -f "${RES}"
  local OK
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
  local OK
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
  local OK
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
  ls "${DIR}"/usr/src |sed -e "s|^\(.*\)-\([0-9.]*\)\$|OK \1 \2|" |grep "^OK" |while read line; do
    MOD=`echo "$line" |cut -d " " -f 2`
    VER=`echo "$line" |cut -d " " -f 3`
    CHK=`echo "${MOD}" |cut -d "-" -f 1`
    if [ "$CHK" == "linux" ]; then
      continue
    fi
    if [ -d "${DIR}"/usr/src/"${MOD}"-"${VER}" ]; then
      echo "${MOD}" "${VER}" "${KER}"
      run_inside dkms add -m "${MOD}" -v "${VER}"
      run_inside dkms build -m "${MOD}" -v "${VER}" -k "${KER}"
      run_inside dkms install -m "${MOD}" -v "${VER}" -k "${KER}"
    fi
  done
  done
}

function avcodec_extra
{
    list=`run_inside aptitude search "^lib.*extra" |cut -d " " -f 4 |grep "^lib[aps][vow].*extra-[0-9]*\$" |xargs echo`
    run_inside apt-get -f -y install $list
}

function wget_html
{
    wtfile=`mktemp --suffix .html`
    wget --convert-links -O "${wtfile}" "$@" 2>/dev/null
    wret="$?"
    if [ "$wret" != "0" ]; then
        return ${wret}
    fi
    cat "${wtfile}"
    rm "${wtfile}"
    return 0
}

function netbeans
{
    src=`wget_html "http://download.netbeans.org/netbeans/" |grep -i 'href="[^"]*/[0-9][0-9.]*/*"' |sed -e 's|.*href="\([^"]*/[0-9][0-9.]*/*\)".*|\1|i' |grep -v "7.2" |tail -n 1`
    if [ -n "$src" ]; then
        echo $src
        src=`wget_html "${src}" |grep -i 'href="[^"]*/[a-z][a-z]*/*"' |tail -n 1 |sed -e 's|.*href="\([^"]*/[a-z][a-z.]*/*\)".*|\1|i'`
        if [ -n "$src" ]; then
        echo $src
        src=`wget_html "${src}zip/" |grep -i 'href="[^"]*netbeans-[^"]*-[0-9]*.zip"' |tail -n 1 |sed -e 's|.*href="\([^"]*netbeans-[^"]*-[0-9]*.zip\)".*|\1|i'`
        if [ -n "$src" ]; then
            echo $src
            wtfile=`mktemp --suffix .zip`
            wget -O "${wtfile}" "$src" 2>/dev/null
            unzip -d "${DIR}/opt" "${wtfile}"
            cat > "${DIR}"/usr/local/bin/netbeans <<EOF
#!/bin/bash
exec /opt/netbeans/bin/netbeans "\$@"
EOF
            chmod 755 "${DIR}"/usr/local/bin/netbeans
            rm "${wtfile}"
        fi
        fi
    fi
}

function eclipse
{
    ECL_BASE="http://ftp.man.poznan.pl/eclipse/technology/epp/downloads/release"
    ECL_DIST=`wget_html "${ECL_BASE}/release.xml" |grep -i "<present>" |sed -e "s|<present>\([^<]*\)</present>|\1|" |tail -n 1`
    src=`wget_html "${ECL_BASE}/${ECL_DIST}" |grep -i '.*-java-.*linux.*x86_64.*tar.gz"' | sed -e 's|.*href="\([^"]*-java-[^"]*linux[^"]*x86_64[^"]*tar.gz\)".*|\1|i' |tail -n 1`
    if [ -n "$src" ]; then
        echo $src
        wtfile=`mktemp --suffix .tar.gz`
        wget -O "${wtfile}" "$src" 2>/dev/null
        tar -C "${DIR}/opt" -x -z -f "${wtfile}"
        cat > "${DIR}"/usr/local/bin/eclipse <<EOF
#!/bin/bash
exec /opt/eclipse/eclipse "\$@"
EOF
        chmod 755 "${DIR}"/usr/local/bin/eclipse
        rm "${wtfile}"
    fi
}

function android
{
    src=`wget_html "http://developer.android.com/sdk/index.html" |grep -i 'href="[^"]*linux[^"]*tgz"' |tail -n 1 |sed -e 's|.*href="\([^"]*linux[^"]*tgz\)".*|\1|i'`
    if [ -n "$src" ]; then
        rm -rf "${DIR}"/opt/google/android
        mkdir -p "${DIR}"/opt/google/android
        echo "$src"
        wget "$src" -O - 2>/dev/null | tar -C "${DIR}"/opt/google/android -x -z --strip-components 1
        cat > "${DIR}"/usr/local/bin/android <<EOF
#!/bin/bash
exec /opt/google/android/tools/android "\$@"
EOF
        chmod 755 "${DIR}"/usr/local/bin/android
        list=`run_inside android list sdk --extended |grep 'id:' |sed -e 's|.*"\([^"]*\)".*|\1|'`
        inst=`for elem in $list; do if [[ "$elem" =~ google || "$elem" =~ intel ]]; then echo $elem; fi; done |sort |uniq |tr "\n" ","`

        yes | run_inside android update sdk --no-ui --force --filter ${inst}platform,system-image,tool,platform-tool,doc,sample
        cat > "${DIR}"/usr/local/bin/adb <<EOF
#!/bin/bash
exec /opt/google/android/platform-tools/adb "\$@"
EOF
        chmod 755 "${DIR}"/usr/local/bin/android "${DIR}"/usr/local/bin/adb
    fi
}

function vmware
{
    cp -a vmware/VMware-Player* "${DIR}"/root/vmplayer.sh &&
    chmod 755 "${DIR}"/root/vmplayer.sh &&
    cp -a vmware/patch*.sh "${DIR}"/root/vmpatch.sh &&
    chmod 755 "${DIR}"/root/vmpatch.sh &&
    cp -a vmware/*.patch "${DIR}"/root
    export VMWARE_EULAS_AGREED="yes"
    run_inside /root/vmplayer.sh --console --required
    unset VMWARE_EULAS_AGREED
    run_inside /root/vmpatch.sh
    KERNEL=`ls -1 "${DIR}"/lib/modules |head -n 1`
    for MOD in `ls -1 "${DIR}"/usr/lib/vmware/modules/source |cut -d "." -f 1`; do
        run_inside vmware-modconfig --console --build-mod -k "${KERNEL}" "${MOD}" /usr/bin/gcc /usr/src/linux-headers-"${KERNEL}"/include
    done
}

function cuda_toolkit
{
  cp -a cuda/NVIDIA-Linux*.run "${DIR}"/root/nvidiadriver.run &&
  chmod 755 "${DIR}"/root/nvidiadriver.run &&
  cp -a cuda/cuda_*.run "${DIR}"/root/cuda.run &&
  chmod 755 "${DIR}"/root/cuda.run &&
#  cp -a cuda/cudatoolkit*.run "${DIR}"/root/cudatoolkit.run &&
#  chmod 755 "${DIR}"/root/cudatoolkit.run &&
#  cp -a cuda/gpucomputingsdk*.run "${DIR}"/root/gpusdk.run &&
#  chmod 755 "${DIR}"/root/gpusdk.run

#Options:
#   -help               : Print help message
#   -driver             : Install NVIDIA Display Driver
#   -uninstall          : Uninstall NVIDIA Display Driver
#   -toolkit            : Install CUDA 5.0 Toolkit
#   -toolkitpath=<PATH> : Specify path for CUDA location (default: /usr/local/cuda-5.0)
#   -samples            : Install CUDA 5.0 Samples
#   -samplespath=<PATH> : Specify path for Samples location (default: /usr/local/cuda-5.0/samples)
#   -silent             : Run in silent mode. Implies acceptance of the EULA
#   -verbose            : Run in verbose mode
#   -extract=<PATH>     : Extract individual installers from the .run file to PATH
#   -optimus            : Install driver support for Optimus
#   -override           : Overrides the installation checks (compiler, lib, etc)


  run_inside apt-get -f -y install make perl-modules linux-headers-generic g++-4.4 gcc-4.4 dkms
  for TYPE in generic; do
    echo ${TYPE}
    VER=`ls "${DIR}"/lib/modules |grep "${TYPE}" |sort |tail -n 1`
    if [ -z "${VER}" ]; then
        continue
    fi
    run_inside /root/nvidiadriver.run --no-distro-scripts --no-cc-version-check --no-x-check --no-nouveau-check --no-network --no-runlevel-check --accept-license --no-precompiled-interface --ui=none --no-questions -k "${VER}"
  done
  echo "blacklist nouveau" > "${DIR}"/etc/modprobe.d/nvidia_nouveau.conf
  if [ "$1" != "driver" -o -d "${DIR}"/usr/local/cuda ]; then
      #mkdir -p "${DIR}"/usr/local/cuda
      #run_inside /root/cudatoolkit.run -- --prefix=/usr/local/cuda
      #run_inside /root/gpusdk.run -- --prefix=/usr/local/cuda/NVIDIA_GPU_Computing_SDK --cudaprefix=/usr/local/cuda
      run_inside /root/cuda.run -toolkit -override -silent
      run_inside /root/cuda.run -samples -override -silent
      mkdir -p "${DIR}"/usr/local/cuda/cc
      ln -s /usr/bin/g++-4.6 "${DIR}"/usr/local/cuda/cc/g++
      ln -s /usr/bin/gcc-4.6 "${DIR}"/usr/local/cuda/cc/gcc
      echo 'compiler-bindir  = $(TOP)/cc' >> "${DIR}"/usr/local/cuda/bin/nvcc.profile
      cat > "${DIR}"/usr/local/bin/nvcc <<EOF
#!/bin/bash
exec /usr/local/cuda/bin/nvcc "\$@"
EOF
      chmod 755 "${DIR}"/usr/local/bin/nvcc
      $( cd "${DIR}"/usr/local/bin
      for ef in ../cuda/bin/* ../cuda/open64/bin/* ../cuda/computeprof/bin/computeprof ../cuda/libnvvp/nvvp ../cuda/nvvm/cicc; do
        if [ -x "$ef" ]; then
          ln -s "$ef" "${DIR}"/usr/local/bin
        fi
      done
      ln -s ../cuda/lib64/* "${DIR}"/usr/local/lib
      ln -s ../cuda/extras/CUPTI/lib64/* "${DIR}"/usr/local/lib )
  fi
  rm "${DIR}"/root/{nvidiadriver,cuda,cudatoolkit,gpusdk}.run
  return 0
}

function satori_client
{
  cat > "${DIR}"/root/script.sh <<EOF
#!/bin/bash
mkdir -p /opt/satori
cd /opt/satori
virtualenv --no-site-packages .
source bin/activate
easy_install -U distribute
hg clone --insecure "https://develro:XVxPqc99Rnsf@satori.tcs.uj.edu.pl/hg/satori" /tmp/satori
for i in satori.objects satori.ars satori.client.common satori.tools ; do
  (cd /tmp/satori/\$i ; python setup.py install )
done
EOF
  chmod 755 "${DIR}"/root/script.sh
  run_inside /root/script.sh
  cat > "${DIR}"/usr/local/bin/satori.submit <<EOF
#!/bin/bash
. /opt/satori/bin/activate
exec satori.submit "\$@"
EOF
  chmod 755 "${DIR}"/usr/local/bin/satori.submit
  cat > "${DIR}"/usr/local/bin/satori.console <<EOF
#!/bin/bash
. /opt/satori/bin/activate
exec satori.console "\$@"
EOF
  chmod 755 "${DIR}"/usr/local/bin/satori.console

  cat > "${DIR}"/usr/local/bin/satori.tool <<EOF
#!/bin/bash
exec javaws -J-Xmx256M https://satori.tcs.uj.edu.pl/files/javatool/satori.javatool.jnlp
EOF
  chmod 755 "${DIR}"/usr/local/bin/satori.tool
  rm -rf "${DIR}"/root/script.sh "${DIR}"/tmp/satori
  return 0
}

function build_base
{
  local OK
  OK=0
  finalize
  rm -rf "${DIR}"
  apt_cache="${APTCACHER}/archive.ubuntu.com/ubuntu"
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

function find_missing_keys
{
  rm -rf "${DIR}"/etc/apt/sources.list.d/*
  run_inside aptitude -y update
  find "${DIR}"/var/lib/apt/ -type f | while read l; do
    key=`gpg --verify "$l" 2>&1 |head -n 1|sed -e "s|.* ||"`
    echo "${key}"
    key=`gpg --verify "$l" "$l" 2>&1 |head -n 1|sed -e "s|.* ||"`
    echo "${key}"
  done > "${TMP}/KEYS"
  cat "${TMP}/KEYS" |sort |uniq |sed -e "s|.*[^A-F0-9].*|NO|" |grep -v "NO" |while read key; do
    run_inside apt-key adv --keyserver "${KEYSERVER}" --recv-key "${key}"
#    gpg --ignore-time-conflict --no-options --no-default-keyring --secret-keyring /etc/apt/secring.gpg --trustdb-name /etc/apt/trustdb.gpg --keyring /etc/apt/trusted.gpg --primary-keyring /etc/apt/trusted.gpg --armor --export "${key}" |run_inside apt-key add -
  done
  run_inside aptitude -y update
  return 0
}

function build_judge
{
  local OK
  OK=0
  ( [ -f "${DIR}"_base.squashfs ] || build_base ) &&
  local OK
  use_squash "${DIR}"_base.squashfs &&
  initialize_full &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST} main restricted universe multiverse" > "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-updates main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://security.ubuntu.com/ubuntu ${DIST}-security main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-backports main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.canonical.com/ ${DIST} partner" >> "${SOURCES}" &&
  echo "deb http://ppa.launchpad.net/ubuntu-toolchain-r/test/ubuntu ${DIST} main" >> "${SOURCES}" &&
  echo "Acquire::http::Proxy \"${APTCACHER}\";" > "${DIR}${APTCACHER_CONF}" &&
  run_inside locale-gen "${LOC}" &&
  find_missing_keys &&
#  echo sun-java7-jre shared/accepted-sun-dlj-v1-1 select true | run_inside debconf-set-selections &&
#  echo sun-java7-jdk shared/accepted-sun-dlj-v1-1 select true | run_inside debconf-set-selections &&
  run_inside aptitude -f -y install upstart &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  run_inside apt-get --no-install-recommends -f -y install ${JUDGE} &&
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

function build_checker
{
  local OK
  OK=0
  ( [ -f "${DIR}"_judge.squashfs ] || build_judge ) &&
  use_squash "${DIR}"_judge.squashfs &&
  initialize_full &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  run_inside apt-get --no-install-recommends -f -y install ${CHECKER} &&
  cuda_toolkit &&
  hg clone --insecure "https://develro:XVxPqc99Rnsf@satori.tcs.uj.edu.pl/hg/satori" "${DIR}"/tmp/satori &&
  run_inside /tmp/satori/install_judge.sh &&
  rm -rf "${DIR}"/tmp/satori &&
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

function build_olimp
{
  local OK
  OK=0
  ( [ -f "${DIR}"_basee.squashfs ] || build_base ) &&
  use_squash "${DIR}"_base.squashfs &&
  initialize_full &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST} main restricted universe multiverse" > "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-updates main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://security.ubuntu.com/ubuntu ${DIST}-security main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-backports main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.canonical.com/ ${DIST} partner" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/talkplugin/deb/ stable main" >> "${SOURCES}" &&
  echo "Acquire::http::Proxy \"${APTCACHER}\";" > "${DIR}${APTCACHER_CONF}" &&
  run_inside locale-gen "${LOC}" &&
#  echo sun-java7-jre shared/accepted-sun-dlj-v1-1 select true | run_inside debconf-set-selections &&
#  echo sun-java7-jdk shared/accepted-sun-dlj-v1-1 select true | run_inside debconf-set-selections &&
  find_missing_keys &&
  run_inside aptitude -f -y install upstart &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  (
  run_inside apt-get --no-install-recommends -f -y install ${OLIMP}
  run_inside aptitude -y purge ${FORBID}
  run_inside apt-get --no-install-recommends -f -y install ${OLIMP}
  exit $?
  ) &&
  cuda_toolkit driver &&
  dkms_all &&
  OK=1

  if [ "${OK}" == "1" ]; then
    OK=0
    make_squash "${DIR}"_olimp.squashfs &&
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
  local OK
  OK=0
  ( [ -f "${DIR}"_judge.squashfs ] || build_judge ) &&
  ( [ -f "${DIR}"_checker.squashfs ] || build_checker ) &&
  use_squash "${DIR}"_judge.squashfs &&
  initialize_full &&
#  echo acroread acroread/default-viewer select true | run_inside debconf-set-selections &&
  echo "deb http://dl.google.com/linux/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/talkplugin/deb/ stable main" >> "${SOURCES}" &&
  find_missing_keys &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  (
  run_inside apt-get --no-install-recommends -f -y install ${UZI}
  run_inside aptitude -y purge ${FORBID}
  run_inside apt-get --no-install-recommends -f -y install ${UZI}
  exit $?
  ) &&
  cuda_toolkit driver &&
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
  local OK
  OK=0
  ( [ -f "${DIR}"_uzi.squashfs ] || build_uzi ) &&
  use_squash "${DIR}"_judge.squashfs &&
  initialize_full &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST} main restricted universe multiverse" > "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-updates main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://security.ubuntu.com/ubuntu ${DIST}-security main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.ubuntu.com/ubuntu ${DIST}-backports main restricted universe multiverse" >> "${SOURCES}" &&
  echo "deb http://archive.canonical.com/ ${DIST} partner" >> "${SOURCES}" &&
  echo "deb http://packages.medibuntu.org/ ${DIST} free non-free" >> "${SOURCES}" &&
  echo "deb http://ppa.launchpad.net/ubuntu-toolchain-r/test/ubuntu ${DIST} main" >> "${SOURCES}" &&
  echo "deb http://ppa.launchpad.net/relan/exfat/ubuntu ${DIST} main" >> "${SOURCES}" &&
  echo "deb http://ppa.launchpad.net/caffeine-developers/ppa/ubuntu ${DIST} main" >> "${SOURCES}" &&
#  echo "deb http://ppa.launchpad.net/freenx-team/ppa/ubuntu lucid main" >> "${SOURCES}" &&
#  echo "deb http://download.virtualbox.org/virtualbox/debian ${DIST} non-free contrib" >> "${SOURCES}" &&
  echo "deb http://deb.opera.com/opera stable non-free" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://dl.google.com/linux/talkplugin/deb/ stable main" >> "${SOURCES}" &&
  echo "deb http://linux.dropbox.com/ubuntu ${DIST} main" >> "${SOURCES}" &&
  echo "deb http://apt.last.fm/ debian stable" >> "${SOURCES}" &&
  echo "deb http://pkg.jenkins-ci.org/debian binary/" >> "${SOURCES}" &&
  echo "deb http://repository.spotify.com stable non-free" >> "${SOURCES}" && 
  echo "deb http://repo.steampowered.com/steam/ ${DIST} steam" >> "${SOURCES}" &&
  echo "Acquire::http::Proxy \"${APTCACHER}\";" > "${DIR}${APTCACHER_CONF}" &&
  find_missing_keys &&
  run_inside locale-gen "pl_PL.UTF-8" &&
  echo acroread acroread/default-viewer select true | run_inside debconf-set-selections &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  (
    run_inside apt-get -f -y install ${FULL}
    cat > ${DIR}/root/script <<EOF
#!/bin/bash
for package in `echo ${FULL} |tr "\n" " "`; do
  apt-get -f -y install \${package}
done
EOF
    chmod 755 ${DIR}/root/script
    run_inside /root/script
    run_inside aptitude -y purge ${FORBID}
    run_inside apt-get --no-install-recommends -f -y install ${FULL}
    exit 0
  ) &&
  run_inside update-java-alternatives -s java-1.7.0-openjdk-amd64 &&
  (
    cp -a "${MYDIR}"/debs "${DIR}"/root
    cat > "${DIR}"/root/script <<EOF
#!/bin/bash
R=0
echo "debscript"
for deb in /root/debs/*.deb; do
  dpkg -i "\${deb}" || R=1
done
exit "\$R"
EOF
    chmod 755 "${DIR}"/root/script
    run_inside /root/script 
    exit 0
  ) &&
  avcodec_extra &&
  dkms_all &&
  vbox_add &&
  cuda_toolkit &&
  netbeans &&
  eclipse &&
  satori_client &&
  vmware &&
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
  local OK
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
  find_missing_keys &&
  run_inside aptitude -y full-upgrade &&
  run_inside aptitude -y forget-new &&
  (
    run_inside apt-get -f -y install ${SERVER}
    cat > ${DIR}/root/script <<EOF
#!/bin/bash
for package in `echo ${SERVER} |tr "\n" " "`; do
  apt-get -f -y install \${package}
done
for package in `echo ${SERVER} |tr "\n" " "`; do
  apt-get -y build-dep \${package}
done
EOF
    chmod 755 ${DIR}/root/script
    run_inside /root/script
    run_inside aptitude -y purge ${FORBID}
    run_inside apt-get --no-install-recommends -f -y install ${SERVER}
    for service in network-manager winbind atftpd bluetooth lightdm gdm kdm exim4 apt-cacher-ng memcached inetd tinyproxy ntp mysql postgres postgresql saned rlinetd postfix apache2 exim4 vmware vmware-USBArbitrator virtualbox virtualbox-guest-utils jenkins openvpn winbind nginx; do
      run_inside update-rc.d -f $service disable
      if [ -e ${DIR}/etc/init/$service.conf ]; then
          echo "manual" > ${DIR}/etc/init/$service.override
      fi
    done
    exit 0
  ) &&
  (
    cp -a "${MYDIR}"/debs_server "${DIR}"/root
    cat > "${DIR}"/root/script <<EOF
#!/bin/bash
R=0
echo "debscript"
for deb in /root/debs_server/*.deb; do
  dpkg -i "\${deb}" || R=1
done
exit "\$R"
EOF
    chmod 755 "${DIR}"/root/script
    run_inside /root/script 
    exit 0
  ) &&
  (
    cat > "${DIR}"/usr/bin/nxagent <<EOF
#!/bin/bash
NX="/usr/NX"
export PATH="\${NX}/bin:/usr/local/bin:/usr/bin:/bin"
export LD_LIBRARY_PATH="\${NX}/lib"
exec "\${NX}/bin/nxagent" "\$@"
EOF
    chmod 755 "${DIR}"/usr/bin/nxagent
    exit 0
  ) &&
  dkms_all &&
  vbox_add &&
#  android &&
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

if [ "$1" == "debug" ]; then
    initialize_full &&
    #avcodec_extra
    #netbeans
    eclipse
    #cuda_toolkit
    #vmware
    finalize
    exit 0
fi

echo " --- ### $0 ### --- "
echo " Usage: "
echo " $0 squash | bash | call | base | judge | checker | uzi | full | server | clean"
exit 1
