#!/bin/bash

# check network
if [ -z  $(hostname -I) ]; then
    echo "Network error: Local IP address not found" && exit 1
fi

# add smolensk repo
tee /etc/apt/sources.list <<EOF
deb file:///opt/main 1.7_x86-64 contrib main non-free
deb file:///opt/devel 1.7_x86-64 contrib main non-free
EOF
apt-get update
if [ $? -ne 0 ]; then
  echo "Smolensk repo error" && exit 1
fi

# install ansible
apt-get install -y ansible
if [ $? -ne 0 ]; then
  echo "Ansible install error" && exit 1
fi

# run ansible-playbook
cd /media/cdrom/ansible
ansible-playbook main.yml
