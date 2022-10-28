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
    if [ -z  "$2" ]; then
        echo "Parameter error: Multibroker role is not defined" && exit 1
    elif [[ $2 == "leader" ]]; then
        if [ -z  "$3" ]; then
            echo "Parameter error: Database address is not defined" && exit 1
        fi
        if [ -z  "$4" ]; then
            echo "Parameter error: Database port is not defined" && exit 1
        fi
        echo "Insert database (postgresql) username:"
        read DB_USER
        if [ -z  "$DB_USER" ]; then
            echo "Parameter error: Database username is empty" && exit 1
        fi
        echo "Insert database (postgresql) password:"
        read -s DB_PASS
        if [ -z  "$DB_PASS" ]; then
            echo "Parameter error: Database password is empty" && exit 1
        fi
        ansible-playbook broker.yml --extra-vars "broker_mode=multi multibroker_role=leader multibroker_db_host=$3 multibroker_db_port=$4 multibroker_db_user=$DB_USER multibroker_db_pass=$DB_PASS"
        DB_PASS=""
    elif [[ $2 == "manager" ]]; then
        if [ -z  "$3" ]; then
            echo "Parameter error: Multibroker leader address is not defined" && exit 1
        fi
        if [ -z  "$4" ]; then
            echo "Parameter error: Multibroker join token is not defined" && exit 1
        fi
        ansible-playbook broker.yml --extra-vars "broker_mode=multi multibroker_role=manager multibroker_swarm_leader_address=$3 multibroker_swarm_join_token=$4"
    fi
elif [[ $1 == "db" ]]; then
    ansible-playbook broker.yml --extra-vars "broker_mode=db"
else
    ansible-playbook broker.yml --extra-vars "broker_mode=single"
fi