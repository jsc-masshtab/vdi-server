# VeiL Broker 2.1.*

## Создание резервной копии БД

Для создания резервной копии БД необходимо выполнить в терминале следующие команды:

```
sudo supervisorctl stop vdi-pool_worker  
sudo supervisorctl stop vdi-server-8888  
sudo supervisorctl stop vdi-monitor_worker
 
sudo -u postgres pg_dump --clean --if-exists vdi > vdi-2.1.4-backup_date +%Y-%m-%d.%H.%M.sql
 
sudo supervisorctl start vdi-pool_worker  
sudo supervisorctl start vdi-server-8888  
sudo supervisorctl start vdi-monitor_worker
```

## Восстановление БД из резервной копии

Для восстановления БД из резервной копии необходимо в терминале выполнить следующие команды:

```
sudo supervisorctl stop vdi-pool_worker  
sudo supervisorctl stop vdi-server-8888  
sudo supervisorctl stop vdi-monitor_worker
 
sudo -u postgres psql vdi -f vdi-2.1.4-backup_2021-02-20.14.16.sql
 
sudo supervisorctl start vdi-pool_worker  
sudo supervisorctl start vdi-server-8888  
sudo supervisorctl start vdi-monitor_worker
```