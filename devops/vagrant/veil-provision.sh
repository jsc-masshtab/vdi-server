#!/bin/bash

# export DEBIAN_FRONTEND=noninteractive

sudo apt-get install -y sshpass

base_cmd="/var/lib/ecp-veil/cli/app/shell.py api"
ssh_opts="-q -tt -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -oConnectTimeout=5"
controller_ip="192.168.20.110"
node1_ip="192.168.20.111"
root_password="bazalt"
api_user="admin"
api_password="veil"

attempts_count=20
for i in $(seq ${attempts_count}); do
  sleep 5
  echo "attempt ${i} connect to controller ${controller_ip}"
  sshpass -p ${root_password} ssh ${ssh_opts} root@${controller_ip} /var/lib/ecp-veil/cli/app/shell.py hostname
  case $? in
    0)
      sleep 5
      echo "Successfully connected to controller ${controller_ip}, ready to provision"
      break
      ;;
    *)
      # echo "Failed connect to controller ${controller_ip} retcode $?"
      ;;
  esac
done

echo "run Veil provision"
# Добавляем узлы
sshpass -p ${root_password} ssh ${ssh_opts} root@${controller_ip} ${base_cmd} node add ${api_user} ${api_password} ${node1_ip} ${node1_ip} ${root_password} -c ${controller_ip}
# sshpass -p ${root_password} ssh ${ssh_opts} root@${controller_ip} ${base_cmd} node list ${api_user} ${api_password} -c ${controller_ip}

# Добавляем ВМ и шаблон на первом попавшемся активнгом узле
sshpass -p ${root_password} ssh ${ssh_opts} root@${controller_ip} ${base_cmd} domain create ${api_user} ${api_password} domain
sshpass -p ${root_password} ssh ${ssh_opts} root@${controller_ip} ${base_cmd} domain create_template ${api_user} ${api_password} template