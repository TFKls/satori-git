#!/bin/bash
OFFICE=$(dirname "$(readlink -f "$(which "$0")")")
pushd "${OFFICE}"
source ./settings.sh

function cleanup {
    rm -rf "${BASE_DIR}"
}
function run_inside {
    echo "$@"
    chroot "${BASE_DIR}" "$@"
}

cleanup
mkdir -p "${BASE_DIR}"

debootstrap --arch="${ARCH}" --include "${BASE_PACKAGES}" "${DISTRO}" "${BASE_DIR}" "${APTCACHER}/archive.ubuntu.com/ubuntu"
if [ "$?" != "0" ]; then
    cleanup
    exit 1
fi

run_inside locale-gen "${LOCALE}"
if [ "$?" != "0" ]; then
    cleanup
    exit 1
fi

SOURCES="${BASE_DIR}"/etc/apt/sources.list
echo "deb http://archive.ubuntu.com/ubuntu ${DISTRO} main restricted universe multiverse" > "${SOURCES}"
echo "deb http://archive.ubuntu.com/ubuntu ${DISTRO}-updates main restricted universe multiverse" >> "${SOURCES}"
echo "deb http://security.ubuntu.com/ubuntu ${DISTRO}-security main restricted universe multiverse" >> "${SOURCES}"

cat > "${BASE_DIR}"/usr/sbin/policy-rc.d <<EOF
#/bin/sh
exit 101
EOF
run_inside chmod +x /usr/sbin/policy-rc.d

run_inside mkdir -p /usr/local/sbin
cat > "${BASE_DIR}"/usr/local/sbin/apt-get-keys <<EOF
#!/bin/bash
apt-get -y update
find /var/lib/apt -type f |while read l; do
    gpg --verify "\$l" 2>&1 |head -n 1|sed -e "s|.* ||"
    gpg --verify "\$l" "\$l" 2>&1 |head -n 1|sed -e "s|.* ||"
done |sort |uniq |sed -e "s|.*[^A-F0-9].*|NO|" |grep -v "NO" |while read key; do
    apt-key adv --keyserver "${KEYSERVER}" --recv-key "\${key}"
done
apt-get -y update
EOF
run_inside chmod +x /usr/local/sbin/apt-get-keys

run_inside dpkg-divert --local --rename --add /sbin/initctl
run_inside ln -sf /bin/true /sbin/initctl

echo 'force-unsafe-io' > "${BASE_DIR}"/etc/dpkg/dpkg.cfg.d/02apt-speedup

for arch in ${OTHER_ARCHITECTURES}; do
    run_inside dpkg --add-architecture "${arch}"
    if [ "$?" != "0" ]; then
        cleanup
        exit 1
    fi
done

run_inside apt-get-keys
if [ "$?" != "0" ]; then
    cleanup
    exit 1
fi
run_inside apt-get -y dist-upgrade
if [ "$?" != "0" ]; then
    cleanup
    exit 1
fi

run_inside apt-get -y autoremove
run_inside apt-get -y clean
./imgbuild/tcs-remap "${BASE_DIR}"
tar --create --auto-compress --numeric-owner --xattrs --file "${BASE_DIR}.tar.gz" --directory "${BASE_DIR}" .
cleanup

docker rmi tcs:base
cat "${BASE_DIR}.tar.gz" |docker import - tcs
docker tag tcs:latest tcs:base
docker rmi tcs:latest

popd
