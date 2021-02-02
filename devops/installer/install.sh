#!/bin/bash

# install ansible
apt-get install -y /media/cdrom/repo/pool/main/a/ansible/ansible_*.deb

# run ansible-playbook
cd /media/cdrom/ansible
REPO="deb file:///media/cdrom/repo smolensk main"
ansible-playbook main.yml --extra-vars "broker_apt_repo='$REPO'"