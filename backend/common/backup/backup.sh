#!/bin/bash

# Скрипт создаёт бекап БД 'vdi'.
# Для запуска, скрипту требуется передать параметром директорию в которую будет сохранён файла бэкапа:
# sudo ./backup.sh /opt/veil-vdi/other


# Initialise default
USERNAME="postgres"


# Initialise backup directory
BACKUP_DIR=$1
if [ ! $BACKUP_DIR ]; then
    echo "Backup directory not passed as parameter."
    exit
fi


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
echo "Stop 'vdi-vm_manager' service"
sudo service vdi-vm_manager stop
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
echo "Start 'vdi-vm_manager' service"
sudo service vdi-vm_manager start
echo "Start 'vdi-web' service"
sudo service vdi-web start
