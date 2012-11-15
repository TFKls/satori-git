#!/bin/bash

DEST=/usr/local/satori
BIN=/usr/local/bin

OFFICE=$(dirname $(readlink -f $(which $0)))
pushd "$OFFICE"
unset PYTHONPATH

apt-get -y install python-virtualenv python-dev libyaml-dev make patch

rm -Rf "$DEST" && mkdir "$DEST" && pushd "$DEST" || exit 1
virtualenv --no-site-packages . &&
source bin/activate &&
easy_install -U distribute || exit 1 
popd

for i in satori.objects satori.ars satori.client.common satori.tools ; do
    pushd "$i" || exit 1; python setup.py install; popd
done

cat > "$BIN/satori.submit" <<EOF
#!/bin/bash

source "$DEST/bin/activate"

exec "$DEST/bin/satori.submit" "\$@"
EOF
&&
chmod a+x "$BIN/satori.submit" || exit 1

popd
