NOTE: manage.sh only for dev

Запускаем сервер командой start, после чего можно обновлять всё на лету командой update

Пример запуска **cd /opt/veil-vdi/devops && bash manage.py update**
```
  Usage: deploy [options] [command]
  Options:
    -h, --help           output help information
  Commands:
    update               update deploy to the latest release / apply db migrations
    curr[ent]            output current release commit
    start                start front and back with nohup
```
