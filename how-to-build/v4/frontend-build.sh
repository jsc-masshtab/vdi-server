#!/bin/bash
WORKSPACE="/veil-broker"
PRJNAME="veil-broker-frontend"
DEB_ROOT="$WORKSPACE/devops/deb"

# set version
sed -i "s:%%VER%%:${VERSION}-1:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"

# npm build
cd ${WORKSPACE}/frontend
rm -rf node_modules && cp -r /node_modules .
npm run build -- --prod

# copy files
mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"
cp -r ${WORKSPACE}/frontend/dist/frontend/* "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"

# build deb
make -C ${DEB_ROOT}/${PRJNAME}