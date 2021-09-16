#!/bin/bash

# check network
if [ -z  $(hostname -I) ]; then
    echo "Network error: Local IP address not found"
    exit 1
fi

# install ansible
apt-get install -y /media/cdrom/repo/pool/main/a/ansible/ansible_*.deb

# run ansible-playbook
cd /media/cdrom/ansible
REPO="deb [trusted=yes] file:///media/cdrom/repo smolensk main"
ansible-playbook main.yml --extra-vars "broker_apt_repo='$REPO'"

# rollback apache2ctl
sed -i '/sleep 5/d' /usr/sbin/apache2ctl