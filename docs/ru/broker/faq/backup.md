# Резервные копии БД

## VeiL Broker 2.1.*

### Создание резервной копии БД
```
sudo supervisorctl stop vdi-pool_worker
sudo supervisorctl stop vdi-server-8888
sudo supervisorctl stop vdi-monitor_worker
 
sudo -u postgres pg_dump --clean --if-exists vdi > vdi-2.1.4-backup_`date +%Y-%m-%d.%H.%M`.sql
 
sudo supervisorctl start vdi-pool_worker
sudo supervisorctl start vdi-server-8888
sudo supervisorctl start vdi-monitor_worker
```

### Восстановление БД из резервной копии на вновь установленном брокере
```
sudo supervisorctl stop vdi-pool_worker
sudo supervisorctl stop vdi-server-8888
sudo supervisorctl stop vdi-monitor_worker
 
sudo -u postgres psql vdi -f vdi-2.1.4-backup_2021-02-20.14.16.sql
 
sudo supervisorctl start vdi-pool_worker
sudo supervisorctl start vdi-server-8888
sudo supervisorctl start vdi-monitor_worker
```

## VeiL Broker 2.2.*

### Создание резервной копии БД
```
sudo service vdi-web stop
sudo service vdi-pool_worker stop
sudo service vdi-monitor_worker stop
 
sudo -u postgres pg_dump --clean --if-exists vdi > vdi-2.2.1-backup_`date +%Y-%m-%d.%H.%M`.sql
 
sudo service vdi-web start
sudo service vdi-pool_worker start
sudo service vdi-monitor_worker start`
```

### Восстановление БД из резервной копии на вновь установленном брокере
```
sudo service vdi-web stop
sudo service vdi-pool_worker stop
sudo service vdi-monitor_worker stop
 
sudo -u postgres psql vdi -f vdi-2.2.1-backup_2021-02-20.14.16.sql
 
sudo service vdi-web start
sudo service vdi-pool_worker start
sudo service vdi-monitor_worker start
```

## VeiL Broker 3.*

!!! warning "Смена мажорной версии"
    Версия **VeiL Broker 3.0.0** и выше не имеет обратной совместимости с предыдущими версиями брокера. В случае необходимости
    переноса рекомендуется установить параллельную установку с **VeiL Broker 3.0.0** (после обновления **ECP VeiL**) и 
    воспроизвести заданные ранее настройки. Если данный сценарий не подходит, необходимо обратиться в АО "НИИ "Масштаб" 
    http://staff.mashtab.org.

### Создание резервной копии БД в директории по умолчанию
!!! note "Примечание"
    Директория по умолчанию определяется параметром `BACKUP_DIR` в файле **/opt/veil-vdi/app/common/backup/backup.config**.

Следующая команда создаст файл резервной копии БД с именем вида **ДД-ММ-ГГГГ_чч-мм-сс_vdi_backup.sql** в директории по умолчанию.
```
sudo /opt/veil-vdi/app/common/backup/backup.sh
```

### Создание резервной копии БД с указанием директории

Следующая команда создаст файл резервной копии БД с именем вида **ДД-ММ-ГГГГ_чч-мм-сс_vdi_backup.sql** в директории **/home/user**.
```
sudo /opt/veil-vdi/app/common/backup/backup.sh /home/user
```

### Восстановление БД из резервной копии на вновь установленном брокере

Следующая команда запустит восстановление БД из файла резервной копии **31-12-2021_15-05-35_vdi_backup.sql**, расположенного в директории по умолчанию.
```
sudo /opt/veil-vdi/app/common/backup/restore.sh 31-12-2021_15-05-35_vdi_backup.sql
```

Так же возможен запуск восстановления БД из файла резервной копии, если скрипту передать полный путь файла.
Следующая команда запустит восстановление БД из файла резервной копии **31-12-2021_15-05-35_vdi_backup.sql**, расположенного в директории **/home/user**.
```
sudo /opt/veil-vdi/app/common/backup/restore.sh /home/user/31-12-2021_15-05-35_vdi_backup.sql
```