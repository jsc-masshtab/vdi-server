# Инструкция по сборке vdi-frontend
## Подготова
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
## Сборка
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