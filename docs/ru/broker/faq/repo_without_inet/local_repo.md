# Обновление через создание локальной копии репозитория

Обновление осуществляется путем создания локального репозитория в виртуальной инфраструктуре.

Данные действия производятся на ОС **Debian** версии **9** или **10**.


!!! note "Примечание"
    Актуальные адреса и названия для репозиториев необходимо запросить у службы поддержки перед обновлением.

1. Создать виртуальную машину в разделе "Виртуальные машины".
2. Выполнить установку ОС **Debian** версии **9** или **10** и настройку сети виртуальной машины.
3. Установить утилиту **_apt-mirror_** для создания локального зеркала репозитория на выделенный для этого сервер:
    ```
    apt-get update
    apt-get install apt-mirror -y
    ```
4. Привести конфигурационный файл **_/etc/apt/mirror.list_** к виду:
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
5. Создать локальное зеркало репозитория. Начнется загрузка пакетов, может занять продолжительное время, в зависимости от скорости вашего канала:
    ```
    su - apt-mirror -c apt-mirror
    ```
6. Установить **_nginx_** на тот же самый сервер:
    ```
    apt-get install nginx -y
    ```
7. Привести конфигурационный файл, находящийся в **_/etc/nginx/sites-enabled/default_**, к виду:
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
8. Обновить конфигурацию **_nginx_**:
    ```
    nginx -s reload
    ```
9.  Подключиться к ВМ, на которую установлен **Veil-Broker**, по протоколу SSH или по протоколу SPICE/VNC через Web-интерфейс ECP VeiL, и выполнить вход от имени учетной записи администратора (по умолчанию ** astravdi:Bazalt1!** ), указав значение **Integrity level** равное **_63_** или **Уровень целостности** - **_Высокий_** (для графического режима).
10. Прописать репозитории на серверах **VeiL Broker**, для этого создать файл ```/etc/apt/sources.list.d/veil-broker.list``` с содержанием:
    ```
    deb http://{LOCAL_REPO_SERVER_IP}/{REPO_NAME} smolensk main
    ```
11. Обновить списки пакетов командой: `apt-get update`.
12. Выполнить обновление пакетной базы командой: `apt-get upgrade -y`.