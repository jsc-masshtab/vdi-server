#!/bin/bash
WORKSPACE="/veil-broker"
PRJNAME="veil-connect-web"
DEB_ROOT="$WORKSPACE/devops/deb"

# set version
sed -i "s:%%VER%%:${VERSION}-1:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"

# npm build
cd ${WORKSPACE}/frontend
rm -rf node_modules && cp -r /node_modules .
npm run build -- --project=thin-client --prod --base-href /thin-client/

# copy files
mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi"
cp -r ${WORKSPACE}/frontend/dist/thin-client ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/

# build deb
make -C ${DEB_ROOT}/${PRJNAME}