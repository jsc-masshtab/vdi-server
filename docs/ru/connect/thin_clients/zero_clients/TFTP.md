# Настройка TFTP

Для осуществления сетевой загрузки необходимо настроить TFTP на сервере, адрес которого указан в конфигурации DHCP. 

## Пример настройки TFTP

1. Установите TFTP-сервер и Xinetd на ваш сервер, выполнив следующую команду:

!!! example "Для дистрибутивов, использующих менеджер пакетов apt"
    ```
    sudo apt-get install tftp-server xinetd 
    ```
!!! example "Для дистрибутивов, использующих менеджер пакетов yum"
    ```
    sudo yum tftp-server xinetd 
    ```
    
2. Приведите файл конфигурации `/etc/xinetd.d/tftp` TFTP сервера к виду

```

service tftp
{
disable = no
socket_type = dgram
protocol = udp
wait = yes
user = root
server = /usr/sbin/in.tftpd
server_args = -u tftp -s /var/lib/tftpboot #путь до директории, где будет находится загрузчик pxelinux и его конфигурация, а также ядро и начальная файловая система.
}

```

