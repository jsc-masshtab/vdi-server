# Установка и запуск

## Установка сервера управления GM Server {#gmserver-install}

Установка сервера управления осуществляется согласно ["Руководству администратора"](https://lk.getmobit.ru/cabinet-user/download-doc/49).

!!! attention "Внимание!"
    Для выполнения работ по инсталляции, обновлению, и перезапуску Сервера управления, установки TLS/SSL сертификатов и настройки параметров операционной системы, необходим доступ к виртуальной машине по ssh (openssh, PUTTY и др. программы) с правами суперпользователя (root). Штатная эксплуатация Сервера управления осуществляется только с использованием веб-консоли Сервера управления.

1. Установите Docker CE [согласно руководству](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

1. Установите пакет сервера управления пользователем с правами суперпользователя (root): 

    ```
    sudo dpkg -i gmserver_[VERSION]_amd64.deb
    ```
    где [VERSION] — номер версии.

!!! attention "Внимание!"
    Все действия выполняются пользователем с правами суперпользователя (root).
    Для выполнения команд и настроек с правами суперпользователя (root) рекомендуется использовать команду **sudo**.
    Пароль для суперпользователя (root) должен формироваться, храниться и меняться в соответствии с парольными политиками, принятыми в организации.

## Установка системы мониторинга GM Server Monitoring {#gmservmon-install}

Установка сервера управления осуществляется согласно ["Руководству администратора"](https://lk.getmobit.ru/cabinet-user/download-doc/49).

1. Установите пакет сервиса мониторинга:

    ```
    dpkg -i gmserver-monitoring_[VERSION]_amd64.deb
    ```
    где [VERSION] — номер версии.

1. Отредактируйте файл **/usr/local/etc/getmobit/docker/config.env** следующим образом:  

    ```
    ELASTIC_HOST=getmobit.example.site  
    FLUENTD_HOST=getmobit.example.site  
    ...  
    JWT_SECRET_KEY=<Произвольная строка>  
    ```
    Первые две строки необходимо добавить: они содержат DNS имя сервера, на котором запущен сервис мониторинга.  <Произвольная строка> — это набор символов длиной до 1024 элементов. Их следует задать самостоятельно. Чем длиннее строка, тем ключ надежнее.

## Первичный запуск сервера {#gmserver-firstrun}

Запустите сервер управления GM Server выполнив следующую команду:

```
systemctl start gmserver
```

Загрузка может занимать до 5 минут. После запуска сервера необходимо выполнить его настройку руководствуясь пунктом [Настройка сервера управления GM Server](../gm_setup) настоящего руководства.