#!/bin/bash

# create apt repo
su aptly <<'EOF'
WORKSPACE="/veil-broker"
DEB_ROOT="$WORKSPACE/devops/deb"

aptly repo create broker_iso
aptly repo add broker_iso ${DEB_ROOT}/veil-broker-backend/*.deb \
                          ${DEB_ROOT}/veil-broker-frontend/*.deb \
                          ${DEB_ROOT}/veil-connect-web/*.deb \
                          ${DEB_ROOT}/veil-broker-docs/*.deb \
                          /debs/*.deb && \
aptly publish repo -skip-signing=true -distribution="1.7_x86-64" broker_iso
EOF

# copy files
WORKSPACE="/veil-broker"
DATE=$(date '+%Y%m%d%H%M%S')
ISO_NAME="veil-broker-${VERSION}-${DATE}"

mkdir -p $WORKSPACE/iso/repo
rsync -aq  /home/aptly/.aptly/public/pool $WORKSPACE/iso/repo/
rsync -aq  /home/aptly/.aptly/public/dists $WORKSPACE/iso/repo/

cd $WORKSPACE
cp -r devops/ansible iso/ansible
rm -f iso/ansible/*.png iso/ansible/*.md iso/ansible/LICENSE
cp devops/installer/install.sh iso

genisoimage -o ./${ISO_NAME}.iso -V veil-broker -R -J ./iso