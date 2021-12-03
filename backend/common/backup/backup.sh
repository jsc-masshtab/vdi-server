#!/bin/bash

# Скрипт создаёт бекап БД 'vdi'.


# Load config
SCRIPTPATH=$(cd ${0%/*} && pwd -P)
source $SCRIPTPATH/backup.config


# Initialise default
if [ ! $USERNAME ]; then
	USERNAME="postgres"
fi;


# Stop services
echo "Stop 'vdi-monitor_worker' service"
sudo service vdi-monitor_worker stop
echo "Stop 'vdi-pool_worker' service"
sudo service vdi-pool_worker stop
echo "Stop 'vdi-web' service"
sudo service vdi-web stop


# Start backup
echo "Creating backup"
sudo -u "$USERNAME" pg_dump --clean --if-exists vdi > $BACKUP_DIR$(date +"%d-%m-%Y_%H-%M-%S")_vdi_backup.sql


# Start services
echo "Start 'vdi-monitor_worker' service"
sudo service vdi-monitor_worker start
echo "Start 'vdi-pool_worker' service"
sudo service vdi-pool_worker start
echo "Start 'vdi-web' service"
sudo service vdi-web start
