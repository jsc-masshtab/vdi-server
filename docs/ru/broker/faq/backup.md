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