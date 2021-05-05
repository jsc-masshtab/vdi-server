# Обновление VDI Broker

## Ручное обновление через Интернет
!!! warning ""
    Процесс обновления занимает не более 5 минут, во время обновления - сервис будет недоступен.

1. Войдите в систему и активируйте режим администратора
1. Загрузите последние версии пакетов VDI Broker
1. Остановите сервисы
1. Выполните установку пакетов
1. Активируйте сервисы
1. Убедитесь, что Web-интерфейс доступен

!!! example "Пример установки обновлений"
    ```
    $ sudo su
    # wget https://veil-update.mashtab.org/vdi/pool/main/v/vdi-backend/vdi-backend_2.1.4-deb9-152_amd64.deb
    # wget https://veil-update.mashtab.org/vdi/pool/main/v/vdi-frontend/vdi-frontend_2.1.4-deb9-127_amd64.deb
    # supervisorctl stop all && service nginx stop
    # export PYTHONPATH=/opt/veil-vdi/app
    # apt install ./vdi-backend_2.1.4-deb9-152_amd64.deb
    # cd /opt/veil-vdi/app/common/migrations && /opt/veil-vdi/env/bin/alembic upgrade head
    # cd /home/user && apt install ./vdi-frontend_2.1.4-deb9-127_amd64.deb
    # supervisorctl start all && service nginx start
    ```

!!! warning "Обновление до 2.1.4"
    При обновлении до версии **2.1.4** расширяются настройки **Службы каталогов**. Если она была добавлена до обновления
    2.1.4, необходимо убедиться, что в поле **Класс объекта домена (dc)** указаны корректные значения вида 
    **dc=domain, dc=local**.  
    Если ранее были созданы пулы с параметром **Наименование групп для добавления ВМ в AD**, убедитесь в корректности
    параметров. Подробности описаны в разделе [Службы каталогов](../active_directory/info.md)