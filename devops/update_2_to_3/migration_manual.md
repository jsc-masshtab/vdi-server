## Пошаговая инструкция миграции данных VeiL Broker 2 -> 3

Перед началом миграции нужно убедиться, что все контроллеры активны и к ним можно подключиться.

### Команды для запуска на версии 2
1. Подключиться к серверу на котором размещен VeiL VDI 2.1.4
```
если используется более ранняя версия, необходимо сначала обновить ее до 2.1.4
```

2. Разместить файл broker_v2.py в каталоге /opt/veil-vdi/app/ 
```
полный путь до файла - /opt/veil-vdi/app/broker_v2.py
```

3. Обновить версию **veil-api-client**
```
/opt/veil-vdi/env/bin/python3 -m pip install 'veil-api-client==2.2.1' --force-reinstall
```

4. Запустить скрипт подготовки экспорта
```
export PYTHONPATH=/opt/veil-vdi/app && cd /opt/veil-vdi/app && /opt/veil-vdi/env/bin/python broker_v2.py
```

5. Сформировать sql-дампы для переноса
```
sudo -u postgres pg_dump vdi --column-inserts --no-owner -a -t user_for_export -t group -t mapping -t entity > /tmp/broker_pt_1.sql
sudo -u postgres pg_dump vdi --column-inserts --no-owner -a -t controller -t authentication_directory -t group_role -t pool_for_export -t entity_owner > /tmp/broker_pt_2.sql
sudo -u postgres pg_dump vdi --column-inserts --no-owner -a -t user_groups -t user_role -t automated_pool -t group_authentication_directory_mappings -t static_pool -t vm > /tmp/broker_pt_3.sql
```

6. Выполните перенос получившихся файлов
```
/tmp/broker_pt_1.sql
/tmp/broker_pt_2.sql
/tmp/broker_pt_3.sql
```

### Команды для запуска на версии 3
1. Подключиться к серверу на котором размещен VeiL VDI 3.0.0
```
* Если планируется использовать версию новее - сначала нужно будет выполнить установку 3.0.0
* ssh-подключение к версии 3.0.0 заблокировано - используйте SPICE/VNC управление с контроллера ECP VeiL.
```

2. Разместить файл broker_v3.py в каталоге /opt/veil-vdi/app/
```
полный путь до файла - /opt/veil-vdi/app/broker_v3.py
```

3. Разместите дампы на сервере в каталоге tmp
```
Дампы должны быть загружены в каталог к которому будет доступ у пользователя vdiadmin.
/tmp/broker_pt_1.sql
/tmp/broker_pt_2.sql
/tmp/broker_pt_3.sql 
```

4. Запустите скрипт импорта данных
```
export PYTHONPATH=/opt/veil-vdi/app && cd /opt/veil-vdi/app && sudo -u vdiadmin /opt/veil-vdi/env/bin/python broker_v3.py
```

5. Задайте вновь созданным заблокированным пользователем пароли
```
На момент миграции в версии 3.0.0 не должно быть иных пользователей, кроме, vdiadmin.
```