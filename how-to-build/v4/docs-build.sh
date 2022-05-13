#!/bin/bash
WORKSPACE="/veil-broker"
PRJNAME="veil-broker-docs"
DEB_ROOT="$WORKSPACE/devops/deb"

# set version
sed -i "s:%%VER%%:${VERSION}-1:g" "${DEB_ROOT}/${PRJNAME}/root/DEBIAN/control"

# generate docs
cd ${WORKSPACE}/docs
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
/usr/local/bin/mkdocs build -f toc.yaml -d ./docs

# copy files
mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi"
cp -r ./docs "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi"

# build deb
make -C ${DEB_ROOT}/${PRJNAME}