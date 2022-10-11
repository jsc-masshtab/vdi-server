#!/bin/bash

# Скрипт восстанавливает БД из бэкапа.
# Для запуска, скрипту требуется передать параметром  файл бэкапа:
# sudo ./restore.sh  /opt/veil-vdi/other/03-12-2021_15-38-24_vdi_backup.sql


# Initialise default
USERNAME="postgres"


# Initialise backup file
BACKUP_FILE=$1
if [ ! $BACKUP_FILE ]; then
    echo "Backup file not passed as parameter."
    exit
fi


# Stop services
echo "Stop 'vdi-monitor_worker' service"
sudo service vdi-monitor_worker stop
echo "Stop 'vdi-pool_worker' service"
sudo service vdi-pool_worker stop
echo "Stop 'vdi-vm_manager' service"
sudo service vdi-vm_manager stop
echo "Stop 'vdi-web' service"
sudo service vdi-web stop


# Start restore
echo "Starting restore from '$BACKUP_FILE'"
sudo -u "$USERNAME" psql vdi -f "$BACKUP_FILE"


# Start services
echo "Start 'vdi-monitor_worker' service"
sudo service vdi-monitor_worker start
echo "Start 'vdi-pool_worker' service"
sudo service vdi-pool_worker start
echo "Start 'vdi-vm_manager' service"
sudo service vdi-vm_manager start
echo "Start 'vdi-web' service"
sudo service vdi-web start