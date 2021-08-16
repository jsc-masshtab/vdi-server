# Обновление инфраструктуры при отсутствии доступа к сети Интернет

- Вариант 1 (рекомендуемый). Через установочный iso-образ.
- Вариант 2. Через виртуальный диск формата **_qcow2_**.
- Вариант 3. Создание локального репозитория.

## Вариант 1.
1. Зайти в ЛК на портале АО «НИИ «Масштаб» https://lk.mashtab.org/ и сделать запрос на установочный iso-образ для нужной версии VeiL Broker.
2. Загрузить образ на свой компьютер.
3. Войти в систему, на которой установлен VeiL Broker, указав значение **Integrity level** равное **_63_** или 
   **Уровень целостности** - **_Высокий_** (для графического режима).
3. Подключить образ к машине, где установлен VeiL Broker.
4. Выполнить команды для обновления VeiL Broker:
    ```
    sudo mount /media/cdrom
    cd
    sudo bash /media/cdrom/install.sh
    sudo umount /media/cdrom
    ```
## Вариант 2. Создание локального репозитория для обновления продуктов VeiL без использования ресурсов Интернета

1. Зайти в ЛК на портале АО «НИИ «Масштаб» https://lk.mashtab.org/ и сделать запрос на виртуальный диск с обновлениями для нужной версии VeiL Broker формата qcow2
2. Загрузить диск на свой компьютер.
3. Создать ВМ с этим диском.
4. Настроить сеть в ВМ (логин **_root_**, без пароля).
5. Прописать репозитории (название репозитория уточнить в службе поддержки) на серверах VeiL Broker, для этого создать файл `/etc/apt/sources.list.d/veil-broker.list` с содержанием:
    ```
    deb http://{VM_IP_ADDRESS}/{REPO_NAME} smolensk main
    ```
6. Обновить списки пакетов командой: `apt-get update`.
7. Выполнить обновление пакетной базы командой: `apt-get upgrade -y`.

## Вариант 3.

Данные действия производятся на ОС Debian версии 9 или 10.

Актуальные адреса и названия для репозиториев можно получить у службы поддержки.

1. Установить утилиту **_apt-mirror_** для создания локального зеркала репозитория на выделенный для этого сервер:
    ```
    apt-get update
    apt-get install apt-mirror -y
    ```
2. Привести конфигурационный файл **_/etc/apt/mirror.list_** к виду:
    ```
    ############# config ##################
    #
    # set base_path    /var/spool/apt-mirror
    #
    # set mirror_path  $base_path/mirror
    # set skel_path    $base_path/skel
    # set var_path     $base_path/var
    # set cleanscript $var_path/clean.sh
    # set defaultarch  <running host architecture>
    # set postmirror_script $var_path/postmirror.sh
    # set run_postmirror 0
    set nthreads     20
    set _tilde 0
    #
    ############# end config ##############
    
    deb http://veil-update.mashtab.org/{REPO_NAME} smolensk main
    
    clean http://veil-update.mashtab.org/{REPO_NAME}
    ```
3. Создать локальное зеркало репозитория. Начнется загрузка пакетов, может занять продолжительное время, в зависимости от скорости вашего канала:
    ```
    su - apt-mirror -c apt-mirror
    ```
4. Установить **_nginx_** на тот же самый сервер:
    ```
    apt-get install nginx -y
    ```
5. Привести конфигурационный файл, находящийся в **_/etc/nginx/sites-enabled/default_**, к виду:
    ```
    server {
        listen 80 default_server;
    
        root /var/spool/apt-mirror/mirror/veil-update.mashtab.org;
    
        server_name _;
    
        location / {
            try_files $uri $uri/ =404;
            autoindex on;
        }
    }
    ```
6. Обновить конфигурацию **_nginx_**:
    ```
    nginx -s reload
    ```
7. Прописать репозитории на серверах VeiL Broker, для этого создать файл **_/etc/apt/sources.list.d/veil-broker.list_** с содержанием:
    ```
    deb http://{LOCAL_REPO_SERVER_IP}/{REPO_NAME} smolensk main
    ```
8. Обновить списки пакетов командой: `apt-get update`.
9. Выполнить обновление пакетной базы командой: `apt-get upgrade -y`.