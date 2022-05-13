# Инструкция по сборке VeiL Broker версии 4
## Подготовка
0. Сборка производится в ОС `Astra Linux Smolensk 1.7`
1. Все действия производятся от имени пользователя `root`
2. Дополнительно к ОС должен быть установлен пакет `docker.io`, для его установки вставьте в устройство чтения компакт-дисков РМС компакт-диск с дистрибутивом операционной системы `Astra Linux Smolensk 1.7` и выполните команды:
```
mount /media/cdrom
apt-get update
apt-get install docker.io -y
umount /media/cdrom
```
3. Создать рабочий каталог, в который будут скопированы исходные тексты, с помощью команды:
```
mkdir /tmp/veil-broker
```
Вставить в устройство чтения компакт-дисков РМС компакт-диск с исходными текстами, смонтировать и скопировать содержимое диска в рабочий каталог с помощью команд:
```
mount /media/cdrom
cp -a /media/cdrom/* /tmp/veil-broker
```
Размонтировать компакт-диск с исходными текстами командой:
```
umount /media/cdrom
```
4. Вставить в устройство чтения компакт-дисков РМС технологический компакт-диск, смонтировать и установить сборочный docker-образ с помощью команд:
```
mount /media/cdrom
docker load --input /media/cdrom/veil-broker-builder-4.0.0.tar
```
Размонтировать технологический компакт-диск командой:
```
umount /media/cdrom
```
## Сборка deb-пакетов
### veil-broker-backend
0. Установить переменные окружения:
```
export WORKSPACE="/tmp/veil-broker"
```
1. Выполнить команду для сборки deb-пакета:
```
docker run -it --rm -v $WORKSPACE/how-to-build/v4/backend-build.sh:/backend-build.sh -v $WORKSPACE:/veil-broker veil-broker-builder:4.0.0 bash backend-build.sh
```
### veil-broker-frontend
0. Установить переменные окружения:
```
export WORKSPACE="/tmp/veil-broker"
```
1. Выполнить команду для сборки deb-пакета:
```
docker run -it --rm -v $WORKSPACE/how-to-build/v4/frontend-build.sh:/frontend-build.sh -v $WORKSPACE:/veil-broker veil-broker-builder:4.0.0 bash frontend-build.sh
```
### veil-connect-web
0. Установить переменные окружения:
```
export WORKSPACE="/tmp/veil-broker"
```
1. Выполнить команду для сборки deb-пакета:
```
docker run -it --rm -v $WORKSPACE/how-to-build/v4/thin-client-build.sh:/thin-client-build.sh -v $WORKSPACE:/veil-broker veil-broker-builder:4.0.0 bash thin-client-build.sh
```
### veil-broker-docs
0. Установить переменные окружения:
```
export WORKSPACE="/tmp/veil-broker"
```
1. Выполнить команду для сборки deb-пакета:
```
docker run -it --rm -v $WORKSPACE/how-to-build/v4/docs-build.sh:/docs-build.sh -v $WORKSPACE:/veil-broker veil-broker-builder:4.0.0 bash docs-build.sh
```
## Сборка iso-образа
0. Установить переменные окружения:
```
export WORKSPACE="/tmp/veil-broker"
```
1. Выполнить команды для сборки iso-образа:
```
docker run -it --rm -v $WORKSPACE/how-to-build/v4/iso-build.sh:/iso-build.sh -v $WORKSPACE:/veil-broker veil-broker-builder:4.0.0 bash iso-build.sh
```
2. Установочный iso-образ VeiL Broker будет доступен в каталоге: `/tmp/veil-broker`