# Миграция данных VeiL Broker 2.х на версию 3.х

Перед началом миграции нужно убедиться, что все контроллеры активны и к ним можно 
подключиться. Скрипт миграции предоставляется по запросу.

## Команды для запуска на версии 2.x

1. Подключиться к серверу, на котором размещен **VeiL Broker 2.1.4**. 
   
    !!! note "Примечание"
        Если используется более ранняя версия **VeiL Broker**, необходимо сначала обновить ее до 2.1.4.

2. Выполнить установку пакета **_vdi-migration-tool_** 
`sudo dpkg -i vdi-migration-tool_1.0-1_all.deb`

3. Запустить скрипт миграции
`cd /opt/veil-vdi/app && ./migrate.sh -v 2`

4. Выполнить перенос получившихся файлов

      `/tmp/broker_pt_1.sql` 
 
      `/tmp/broker_pt_2.sql` 
 
      `/tmp/broker_pt_3.sql`


## Команды для запуска на версии 3.x

1. Подключиться к серверу, на котором размещен **VeiL Broker 3.0.0**.

    !!! note "Примечание"
        1. Если планируется использовать версию новее, сначала нужно выполнить установку **VeiL Broker 3.0.0**.
        1. Если ssh-подключение к версии 3.0.0 заблокировано, используйте SPICE/VNC 
           управление с контроллера **ECP VeiL**.

2. Разместить дампы памяти на сервере в каталоге **tmp**.

    !!! note "Примечание"
        Дампы памяти должны быть загружены в каталог, к которому будет доступ у пользователя 
        **vdiadmin**.  
        `/tmp/broker_pt_1.sql`   
        `/tmp/broker_pt_2.sql`    
        `/tmp/broker_pt_3.sql`

3. Выполнить установку пакета **vdi-migration-tool** 
`sudo dpkg -i vdi-migration-tool_1.0-1_all.deb`

4. Запустить скрипт миграции
`cd /opt/veil-vdi/app && ./migrate.sh -v 3`

5. Задать пароли вновь созданным заблокированным пользователям. 

    !!! note "Примечание"
        На момент миграции в версии **VeiL Broker 3.0.0** не должно быть иных пользователей, кроме **vdiadmin**.