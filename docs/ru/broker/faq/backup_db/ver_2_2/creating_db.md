# VeiL Broker 2.2.*

## Создание резервной копии БД

Для создания резервной копии БД необходимо выполнить в терминале следующие команды:

```
sudo service vdi-web stop  
sudo service vdi-pool_worker stop  
sudo service vdi-monitor_worker stop  
 
sudo -u postgres pg_dump --clean --if-exists vdi > vdi-2.2.1-backup_date +%Y-%m-%d.%H.%M.sql
 
sudo service vdi-web start  
sudo service vdi-pool_worker start  
sudo service vdi-monitor_worker start
```

## Восстановление БД из резервной копии

Для восстановления БД из резервной копии необходимо в терминале выполнить следующие команды:

```
sudo service vdi-web stop  
sudo service vdi-pool_worker stop  
sudo service vdi-monitor_worker stop 
 
sudo -u postgres psql vdi -f vdi-2.2.1-backup_2021-02-20.14.16.sql
 
sudo service vdi-web start
sudo service vdi-pool_worker start
sudo service vdi-monitor_worker start
```