# Обновление инфраструктуры при отсутствии доступа к сети Интернет

- Вариант 1. Через виртуальный диск формата **qcow2**.
- Вариант 2. Создание локального репозитория.

## Вариант 1. 

1. Зайти в ЛК https://lk.mashtab.org/ и сделать запрос на виртуальный диск с обновлениями для нужной версии **VeiL Connect** формата **qcow2**.
2. Загрузить диск к себе.
3. Создать ВМ с этим диском.
4. Настроить сеть в ВМ (логин **root**, без пароля).
5. Прописать репозитории (название дистрибутива уточнить в службе поддержки) на машинах с  **VeiL Connect**, для этого создать файл:
   
   - Для deb-based систем - `/etc/apt/sources.list.d/veil-connect.list` с содержанием:
     ```
     deb http://{VM_IP_ADDRESS}/veil-connect {DISTRIB} main
     ```
   - Для rpm-based систем - `/etc/yum.repos.d/veil-connect.repo` с содержанием:
  
     `[veil-connect]`  
     `name=VeiL Connect repository`  
     `baseurl=http://{VM_IP_ADDRESS}/veil-connect/linux/yum/el$releasever/$basearch`  
     `gpgcheck=1`  
     `gpgkey=http://{VM_IP_ADDRESS}/veil-connect/linux/yum/RPM-GPG-KEY-veil-connect`  
     `enabled=1`  
     
6. Обновить списки пакетов командой:

    - Для deb-based систем: `apt-get update`.
    - Для rpm-based систем: `yum -y makecache`.
7. Выполнить обновление пакетной базы командой:

    - Для deb-based систем: `apt-get upgrade -y`.
    - Для rpm-based систем: `yum -y update`.

## Вариант 2. Cоздание пользователем локального репозитория для обновления продуктов VeiL без использования ресурсов интернет

Данные действия производятся на ОС **Debian** версии **9** или **10**.

Актуальные адреса и названия для репозиториев можно получить у службы поддержки.

1. Устанавливаем утилиту **wget** для создания локального зеркала репозитория на выделенный для этого сервер:

    `apt-get update`
     
    `apt-get install wget -y`

2. Создаём локальное зеркало репозитория. Начнется загрузка пакетов, может занять продолжительное время, в зависимости от скорости вашего канала:

    `mkdir -p /opt/repo`  
    `wget --recursive --no-parent --no-host-directories --reject='index.html*' -l 0 -P /opt/repo veil-update.mashtab.org/veil-connect/`

3. Устанавливаем **nginx** на тот же самый сервер:
```
apt-get install nginx -y
```
4. Приводим конфигурацию **/etc/nginx/sites-enabled/default** к виду:

    `server {`  
        `listen 80 default_server;`  
        `root /opt/repo;`  
        `server_name _;`  
        `location / {`  
            `try_files $uri $uri/ =404;`  
            `autoindex on;`  
        `}`  
    `}`  

5. Обновляем конфигурацию **nginx**:
```
nginx -s reload
```
6. Прописать репозитории (название дистрибутива уточнить в службе поддержки) на машинах с  **VeiL Connect**, для этого создать файл:
   
    - Для deb-based систем - `/etc/apt/sources.list.d/veil-connect.list` с содержанием:
    ```
    deb http://{LOCAL_REPO_IP_ADDRESS}/veil-connect {DISTRIB} main
    ```
    - Для rpm-based систем - `/etc/yum.repos.d/veil-connect.repo` с содержанием:
    
        `[veil-connect]`  
        `name=VeiL Connect repository`  
        `baseurl=http://{LOCAL_REPO_IP_ADDRESS}/veil-connect/linux/yum/el$releasever/$basearch`  
        `gpgcheck=1`  
        `gpgkey=http://{LOCAL_REPO_IP_ADDRESS}/veil-connect/linux/yum/RPM-GPG-KEY-veil-connect`  
        `enabled=1`  
   
7. Обновить списки пакетов командой:
   
    - Для deb-based систем: `apt-get update`.
    - Для rpm-based систем: `yum -y makecache`.
8. Выполнить обновление пакетной базы командой:
   
    - Для deb-based систем: `apt-get upgrade -y`.
    - Для rpm-based систем: `yum -y update`.