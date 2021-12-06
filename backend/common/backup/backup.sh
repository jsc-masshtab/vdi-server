#!/bin/bash

# Скрипт создаёт бекап БД 'vdi'.
# При запуске, скрипту можно передать параметром директорию: в неё будет сохранён файла бэкапа.
# При запуске скрипта без параметра, для сохранения файла бэкапа будет использована директория из backup.config


# Load config
SCRIPTPATH=$(cd ${0%/*} && pwd -P)
source $SCRIPTPATH/backup.config


# Initialise default
if [ ! $USERNAME ]; then
	USERNAME="postgres"
fi;


# Initialise backup directory
BACKUP_DIR_ARG=$1
if [ ! $BACKUP_DIR_ARG ]; then
    echo "Used default backup directory $BACKUP_DIR"
else
    echo "Used backup directory $BACKUP_DIR_ARG"
    BACKUP_DIR=$BACKUP_DIR_ARG
fi;


# Check '/' at the end of backup directory
case "$BACKUP_DIR" in
*/)
    ;;
*)
    BACKUP_DIR="${BACKUP_DIR}/"
    ;;
esac


# Stop services
echo "Stop 'vdi-monitor_worker' service"
sudo service vdi-monitor_worker stop
echo "Stop 'vdi-pool_worker' service"
sudo service vdi-pool_worker stop
echo "Stop 'vdi-web' service"
sudo service vdi-web stop


# Start backup
echo "Creating backup in $BACKUP_DIR"
sudo -u "$USERNAME" pg_dump --clean --if-exists vdi > $BACKUP_DIR$(date +"%d-%m-%Y_%H-%M-%S")_vdi_backup.sql


# Start services
echo "Start 'vdi-monitor_worker' service"
sudo service vdi-monitor_worker start
echo "Start 'vdi-pool_worker' service"
sudo service vdi-pool_worker start
echo "Start 'vdi-web' service"
sudo service vdi-web start
