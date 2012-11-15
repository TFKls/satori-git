#!/bin/bash

DEST=/usr/local/satori
BIN=/usr/local/bin


OFFICE=$(dirname $(readlink -f $(which $0)))
pushd "$OFFICE"
unset PYTHONPATH

apt-get -y install python-virtualenv python-dev libpopt-dev libcurl4-openssl-dev libpq-dev libyaml-dev libcap-dev make patch

rm -Rf "$DEST" && mkdir "$DEST" && pushd "$DEST" || exit 1
virtualenv --no-site-packages --prompt=\(satori\) . &&
source bin/activate &&
easy_install -U distribute || exit 1
popd

for i in satori.objects satori.ars satori.client.common satori.tools satori.judge ; do
    pushd "$i" || exit 1; python setup.py install; popd
done

pushd satori.judge/runner || exit 1
make runner &&
cp runner "$BIN" || exit 1
popd

cat > "$BIN/satori.judge" <<EOF
#!/bin/bash

source "$DEST/bin/activate"

exec "$DEST/bin/satori.judge_init" "\$@"
EOF
chmod a+x "$BIN/satori.judge" || exit 1

popd
