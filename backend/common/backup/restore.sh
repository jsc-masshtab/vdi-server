#!/bin/bash

# Скрипт восстанавливает БД из бекапа.
# Для запуска скрипту требуется передать параметром имя файла бекапа:
# sudo ./restore.sh  03-12-2021_15-38-24_vdi_backup.sql


# Load config
SCRIPTPATH=$(cd ${0%/*} && pwd -P)
source $SCRIPTPATH/backup.config


# Initialise default
if [ ! $USERNAME ]; then
	USERNAME="postgres"
fi;


# Initialise backup file
BACKUP_FILE=$1
if [ ! $BACKUP_FILE ]; then
    echo "Backup file not passed as parameter."
    exit
fi;


# Check if BACKUP_FILE contains '/'
if [[ "$BACKUP_FILE" == *\/* ]]; then
    BACKUP_PATH=$BACKUP_FILE
else
    BACKUP_PATH=$BACKUP_DIR$BACKUP_FILE
fi


# Stop services
echo "Stop 'vdi-monitor_worker' service"
sudo service vdi-monitor_worker stop
echo "Stop 'vdi-pool_worker' service"
sudo service vdi-pool_worker stop
echo "Stop 'vdi-web' service"
sudo service vdi-web stop


# Start restore
echo "Starting restore from '$BACKUP_PATH'"
sudo -u "$USERNAME" psql vdi -f "$BACKUP_PATH"


# Start services
echo "Start 'vdi-monitor_worker' service"
sudo service vdi-monitor_worker start
echo "Start 'vdi-pool_worker' service"
sudo service vdi-pool_worker start
echo "Start 'vdi-web' service"
sudo service vdi-web start