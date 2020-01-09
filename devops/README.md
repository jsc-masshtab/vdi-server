### manage.sh - обертка для управления сервисами
```
  Usage: bash manage.sh [options] [command]
  Options:
    -h, --help           output help information
  Commands:
    update               update deploy to the latest release / apply db migrations
    curr[ent]            output current release commit
    start                start backend via supervisor and compile frontend for nginx
    truncate_controllers remove all controllers data from db and restart backend
    stop                 stop backend via supervisor
```
###### Обновить кодовую базу из dev и пересобрать фронт:
 1. **ssh vagrant@192.168.20.110** || **ssh bazalt@192.168.6.223**
 2. vagrant || bazalt
 3. **sudo bash /opt/veil-vdi/devops/manage.sh update**
 
###### Просмотр логов
Логи лежат в директории **/var/log/veil-vdi/**
tornado-stdout.log - перехват стандартного stdout

tornado-strerr.log - перехват stderr

###### Просмотр логов в риалтайме
1. **ssh vagrant@192.168.20.110** || **ssh bazalt@192.168.6.223**
2. vagrant || bazalt
3. **sudo tail -f /var/log/veil-vdi/tornado-stdout.log** 