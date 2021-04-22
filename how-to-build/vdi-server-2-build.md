# Инструкция по сборке VeiL Broker версии 2
## vdi-backend
### Подготовка
0. Сборка производится в ОС Debian 9
1. Дополнительно к ОС должны быть установлены следующие пакеты:
```
python3-dev
python3-setuptools
python-dev
gcc
python3-pip
libsasl2-dev
libldap2-dev
libssl-dev
sudo
curl
apt-utils
rsync
```
Выполнить установку этих пакетов:
```
apt update
apt install -y python3-dev python3-setuptools python-dev gcc python3-pip libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils rsync
```
2. Создать рабочий каталог, в который будут скопированы исходные тексты, с помощью команды:
```
mkdir /tmp/vdi-backend
```
Вставить в устройство чтения компакт-дисков РМС компакт-диск с исходными текстами, смонтировать и скопировать содержимое диска в рабочий каталог с помощью команд:
```
mount /media/cdrom
cp -a /media/cdrom/* /tmp/vdi-backend
```
Размонтировать компакт-диск с исходными текстами командой:
```
umount /media/cdrom
```
### Сборка
3. Перейти в каталог с исходными текстами:
```
cd /tmp/vdi-backend
```
Указать версию пакета командой:
```
sed -i "s:%%VER%%:2.0.2:g" "devops/deb/vdi-backend/root/DEBIAN/control"
```
4. Установить зависимости python:
```
/usr/bin/python3 -m pip --no-cache-dir install -U pip
/usr/bin/python3 -m pip --no-cache-dir install 'virtualenv==15.1.0' --force-reinstall
sudo /usr/bin/python3 -m virtualenv devops/deb/vdi-backend/root/opt/veil-vdi/env
cd devops/deb/vdi-backend/root/opt/veil-vdi/app
sudo devops/deb/vdi-backend/root/opt/veil-vdi/env/bin/python -m pip --no-cache-dir install -r requirements.txt
```
5. Перейти в каталог backend и выполнить сборку deb-пакета:
```
cd /tmp/vdi-backend/backend/
chmod +x compilemessages.sh
./compilemessages.sh en
./compilemessages.sh ru
cd ..
make -C "devops/deb/vdi-backend"
```
6. Готовый deb-пакет будет находиться в каталоге `/tmp/vdi-backend/devops/deb/vdi-backend`

## vdi-frontend
### Подготовка
0. Сборка производится в ОС Debian 9
1. Дополнительно к ОС должны быть установлены следующие пакеты:
```
nodejs
gcc
libsasl2-dev
libldap2-dev
libssl-dev
sudo
curl
apt-utils
```
Выполнить установку этих пакетов:
```
echo "deb https://deb.nodesource.com/node_10.x stretch main" > /etc/apt/sources.list.d/nodesource.list
apt update
apt install -y nodejs gcc libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils
```
2. Создать рабочий каталог, в который будут скопированы исходные тексты, с помощью команды:
```
mkdir /tmp/vdi-frontend
```
Вставить в устройство чтения компакт-дисков РМС компакт-диск с исходными текстами, смонтировать и скопировать содержимое диска в рабочий каталог с помощью команд:
```
mount /media/cdrom
cp -a /media/cdrom/* /tmp/vdi-frontend
```
Размонтировать компакт-диск с исходными текстами командой:
```
umount /media/cdrom
```
### Сборка
3. Перейти в каталог с исходными текстами:
```
cd /tmp/vdi-frontend
```
Указать версию пакета командой:
```
sed -i "s:%%VER%%:2.0.2:g" "devops/deb/vdi-frontend/root/DEBIAN/control"
```
4. Установить зависимости nodejs:
```
cd frontend
npm install --unsafe-perm
npm run build -- --prod
```
5. Скопировать установленные зависимости:
```
mkdir -p "devops/deb/vdi-frontend/root/opt/veil-vdi/www"
cp -r /tmp/vdi-frontend/frontend/dist/frontend/* "devops/deb/vdi-frontend/root/opt/veil-vdi/www"
```
6. Выполнить сборку deb-пакета:
```
make -C devops/deb/vdi-frontend
```
7. Готовый deb-пакет будет находиться в каталоге `/tmp/vdi-frontend/devops/deb/vdi-frontend`

## Виртуальная машина
1. Создать новую виртуальную машину с парметрами: 2xCPU, 4gb RAM, HDD 20gb QCOW2
2. Установить на виртуальную машину ОС Debian 9
3. Скопировать deb-пакеты vdi-backend и vdi-frontend в виртуальную машину
4. Установить пакеты vdi:
```
sudo apt update
sudo apt install ./vdi-*.deb -y
```
5. Выгрузить виртуальный жесткий диск в формате QCOW2