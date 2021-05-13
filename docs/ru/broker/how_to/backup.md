# Резервные копии БД

## VeiL Broker 2.1.*

### Создание резервной копии БД
```
sudo supervisorctl stop vdi-pool_worker
sudo supervisorctl stop vdi-server-8888
sudo supervisorctl stop vdi-ws_listener_worker
 
sudo -u postgres pg_dump --clean --if-exists vdi > vdi-2.1.4-backup_`date +%Y-%m-%d.%H.%M`.sql
 
sudo supervisorctl start vdi-pool_worker
sudo supervisorctl start vdi-server-8888
sudo supervisorctl start vdi-ws_listener_worker
```

### Восстановление БД из резервной копии на чистой инсталляции брокера
```
sudo supervisorctl stop vdi-pool_worker
sudo supervisorctl stop vdi-server-8888
sudo supervisorctl stop vdi-ws_listener_worker
 
sudo -u postgres psql vdi -f vdi-2.1.4-backup_2021-02-20.14.16.sql
 
sudo supervisorctl start vdi-pool_worker
sudo supervisorctl start vdi-server-8888
sudo supervisorctl start vdi-ws_listener_worker
```

## VeiL Broker 2.2.*

### Создание резервной копии БД
```
sudo service vdi-web stop
sudo service vdi-pool_worker stop
sudo service vdi-ws_listener stop
 
sudo -u postgres pg_dump --clean --if-exists vdi > vdi-2.2.1-backup_`date +%Y-%m-%d.%H.%M`.sql
 
sudo service vdi-web start
sudo service vdi-pool_worker start
sudo service vdi-ws_listener start`
```

### Восстановление БД из резервной копии на чистой инсталляции брокера
```
sudo service vdi-web stop
sudo service vdi-pool_worker stop
sudo service vdi-ws_listener stop
 
sudo -u postgres psql vdi -f vdi-2.2.1-backup_2021-02-20.14.16.sql
 
sudo service vdi-web start
sudo service vdi-pool_worker start
sudo service vdi-ws_listener start
```

## VeiL Broker 3.0.*

!!! warning "Смена мажорной версии"
    Версия брокера 3.0.* и выше не имеет обратной совместимости с предыдущими версиями брокера. В случае необходимости
    переноса рекомендуется установить параллельную установку с брокером 3.0 (после обновления VeiL ECP) и воспроизвести
    заданные ранее настройки. Если данный сценарий не подходит - необходимо обратиться на http://staff.mashtab.org