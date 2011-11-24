aptitude -y install python-virtualenv python-dev libyaml-dev make patch

rm -R /usr/local/satori
mkdir /usr/local/satori

cd /usr/local/satori

virtualenv --no-site-packages .
source bin/activate
easy_install -U distribute

cp -R /mnt/storage/users/zzzmwm01/satori /tmp/__satori__

cd /tmp/__satori__

for i in satori.objects satori.ars satori.client.common satori.tools ; do
    (cd $i ; python setup.py install )
done

cd /usr/local/bin

cat > satori.submit <<EOF
#!/bin/bash

. /usr/local/satori/bin/activate

exec satori.submit \$@
EOF

chmod a+x satori.submit

rm -R /tmp/__satori__

