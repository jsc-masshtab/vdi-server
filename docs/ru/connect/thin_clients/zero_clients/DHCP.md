# Настройка DHCP

Для получения компьютером АРМ адреса, к которому необходимо обращаться для загрузки PXE загрузчика и ядра ОС с стартовой файловой системой необходимо указать его в конфигурации DHCP сервера.

## Пример конфигурации DHCP

2. Установите на сервер DHCP программу **dhcpd**, которая будет использоваться в качестве DHCP сервера.


    
1. Приведите файл конфигурации программы **dhcpd** ```/etc/dhcp/dhcpd.conf``` к следующему виду:


```

option domain-name-servers 8.8.8.8; #DNS сервера
 
server-name "veil-pxe"
 
subnet 192.168.135.0 netmask 255.255.255.0 #Ваша сеть
{
next-server 192.168.135.1; #адрес tftp сервера
filename "pxelinux.0"; #путь до файла начиная от директории настроенной в TFTP pxelinux.0
option root-path "/srv/public/netinst/current"; #Если nfs сервер находится на одном сервере с tftp.
option domain-name "comp-core-processor-3688be";
default-lease-time 3600;
max-lease-time 3600;
range 192.168.135.100 192.168.135.200; #Диапазон ip адресов для раздачи
}

```

