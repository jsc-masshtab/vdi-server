#!/bin/bash

sed -i s/us\./ru\./g /etc/apt/sources.list
apt-get update -y
apt-get install --no-install-recommends -y sshfs


sudo mkdir /mnt/veil-vdi
sudo sshfs -o allow_other vagrant@192.168.20.112:/opt/veil-vdi /mnt/veil-vdi

# umount /mnt/veil-vdi