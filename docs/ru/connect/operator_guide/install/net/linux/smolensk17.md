# Astra Linux Smolensk 1.7 

Для установки **VeiL Connect** с сервера **НИИ "Масштаб"** на **Astra Linux Smolensk 1.7** необходимо выполнить следующие шаги:

1. Подключить iso-образ основного диска **Astra Linux Smolensk 1.7**, выполнить команды для копирования deb-пакетов в систему:

`sudo mount /media/cdrom`      
`sudo mkdir /opt/main`  
`sudo cp -r /media/cdrom/pool /media/cdrom/dists /opt/main/`  
`sudo umount /media/cdrom`

2. Подключить iso-образ devel-диска **Astra Linux Smolensk 1.7**, выполнить команды для копирования deb-пакетов в систему:

`sudo mount /media/cdrom`  
`sudo mkdir /opt/devel`  
`sudo cp -r /media/cdrom/pool /media/cdrom/dists /opt/devel/`  
`sudo umount /media/cdrom`

3. Настроить локальный apt-репозиторий, привести файл **/etc/apt/sources.list** к виду:

`deb file:///opt/main 1.7_x86-64 contrib main non-free`  
`deb file:///opt/devel 1.7_x86-64 contrib main non-free`  

4. Обновить списки пакетов командой:
```
sudo apt-get update
```

5. Открыть в браузере адрес: https://veil-update.mashtab.org/veil-connect/linux/apt/pool/main/v/veil-connect/ и загрузить deb-пакет последней версии, 
   в названии которого присутствует **~stretch** (например, veil-connect_1.4.1~stretch_amd64.deb).
   
6. Перейти в каталог, в который был загружен deb-пакет на предыдущем шаге и выполнить команду для установки deb-пакета:
```
sudo apt-get install ./veil-connect*stretch*.deb -y
```