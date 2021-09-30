#!/bin/bash

# check network
if [ -z  $(hostname -I) ]; then
    echo "Network error: Local IP address not found" && exit 1
fi

# add smolensk repo
tee /etc/apt/sources.list <<EOF
# deb cdrom:[OS Astra Linux 1.6 smolensk - amd64 DVD ]/ smolensk contrib main non-free
deb file:///opt/main smolensk contrib main non-free
deb file:///opt/devel smolensk contrib main non-free
EOF
apt-get update
if [ $? -ne 0 ]; then
  echo "Smolensk repo error" && exit 1
fi

# install ansible
apt-get install -y /media/cdrom/repo/pool/main/a/ansible/ansible_*.deb
if [ $? -ne 0 ]; then
  echo "Ansible install error" && exit 1
fi

# run ansible-playbook
cd /media/cdrom/ansible
ansible-playbook main.yml

# rollback apache2ctl
sed -i '/sleep 5/d' /usr/sbin/apache2ctl