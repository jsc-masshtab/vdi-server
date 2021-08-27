# Настройка pxelinux

## Пример настройки pxelinux
1. Примонтируйте образ Live-CD с установленным VeiL-Connect к системе командой:

'''bash
mount live-veil-connect-<version>.iso /mnt/
'''

2. Скопиройте файл загрузчика pxelinux в директорию, указанную в конфигурациях TFTP и DHCP (в данном примере '/var/lib/tftpboot/') выполнив команду:

'''bash
cp /mnt/syslinux/pxelinux.0 /var/lib/tftpboot/pxelinux.0
'''

3. Скопируйте файл конфигурации загрузчика syslinux в директорию, указанную в конфигурации TFTP и DHCP выполнив следующую команду:

'''bash
mkdir /var/lib/tftpboot/pxelinux.cfg && cp /mnt/syslinux/isolinux.cfg /var/lib/tftpboot/pxelinux.cfg/default
''' 

4. Скопируйте директорию alt0 содержащую ядро ОС и начальную файловую систему выполнив команду:
'''bash
cp -r /mnt/syslinux/alt0 /var/lib/tftpboot/pxelinux.cfg/
'''

5. Отмонтировать образ командой:
'''bash
umount /mnt/
'''

6. Привести файл конфигурации загрузчика pxelinux '/var/lib/tftpboot/pxelinux.cfg/default' к виду:

'''shell
default live
timeout 100
totaltimeout 100
label live
menu label ^LiveCD (no hard disk needed)
kernel alt0/vmlinuz
append initrd=alt0/full.cz fastboot live changedisk stagename=live ramdisk_size=490013 showopts lowmem vga=normal quiet CONFIG_FILE=http://192.168.135.1/veil_client_settings.ini automatic=method:nfs,network:dhcp tz=Europe/Moscow lang=ru_RU

'''
, где:
* kernel - путь до ядра ОС относительно пути, указанного в конфигурациях TFTP и DHCP
* initrd= путь к начальной файловой системе относительно пути, указанного в конфигурации TFTP и DHCP
* automatic=method:nfs,network:dhcp - способ загрузки корневой файловой системы, если NFS и TFTP сервер находятся на одном сервере. Если NFS и TFTP находятся на разных серверах следует использовать 'automatic=method:nfs,network:dhcp,server:192.168.135.1,directory:/srv/public/netinst/1.img'
* CONFIG_FILE=http://192.168.135.1/veil_client_settings.ini - путь до файла конфигурации veil-connect. Его можно разместить в сети используя любой удобный сопособ, например вебсервер apache. Файл конфигурации можно взять из настроеной системы, он распалагается по адресу ~/.config/VeilConnect/veil_client_settings.ini

## Возможные варианты публикации основной файловой системы

'''
automatic=method:nfs,network:dhcp,server:192.168.135.1,directory:/srv/public/netinst/1.img
automatic=method:ftp,network:dhcp,server:mashtab.org,directory:/srv/public/netinst/
automatic=method:ftp,network:dhcp,server:companyserver,directory:/altlinux,user:XXX,pass:XXX
automatic=method:ftp,interface:eth1,network:dhcp,...
automatic=method:http,network:dhcp,server:192.0.2.2,directory:/netinst/
'''
