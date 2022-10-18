#!/bin/bash
WORKSPACE="/veil-broker"
PRJNAME="veil-broker-backend"
DEB_ROOT="$WORKSPACE/devops/deb"

# copy files
mv /pip/env "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/"
rsync -a ${WORKSPACE}/backend/ "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"
cd "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"

# set VERSION
sed -i "s:%%VER%%:${VERSION}-1:g" "${DEB_ROOT}/${PRJNAME}/root/DEBIAN/control"

# make relocatable env
virtualenv --relocatable ../env

# compilemessages
cd common
chmod +x compilemessages.sh
./compilemessages.sh en
./compilemessages.sh ru
cd ..

# build deb
make -C "${DEB_ROOT}/${PRJNAME}"