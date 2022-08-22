#!/bin/bash

# check network
if [ -z  "$(hostname -I)" ]; then
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
if [[ $1 == "multi" ]]; then
    if [[ $2 == "manager" ]]; then
        ansible-playbook broker.yml --extra-vars "broker_mode=multi multibroker_role=manager"
    elif [[ $2 == "worker" ]]; then
        if [ -z  "$3" ]; then
            echo "Parameter error: Multibroker manager address is not defined" && exit 1
        fi
        if [ -z  "$4" ]; then
            echo "Parameter error: Multibroker manager join token is not defined" && exit 1
        fi
        ansible-playbook broker.yml --extra-vars "broker_mode=multi multibroker_role=worker multibroker_swarm_manager_address=$3 multibroker_swarm_join_token=$4"
    fi
else
    ansible-playbook broker.yml
fi