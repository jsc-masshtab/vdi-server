# Инструкция по сборке VeiL Broker версии 3
## Подготовка
0. Сборка производится в ОС `Debian 9`
1. Сборочная машина должна иметь доступ к сети `Интернет`
2. Все действия производятся от имени пользователя `root`
3. Дополнительно к ОС должны быть установлены следующие пакеты:
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
genisoimage
wget
gettext
aptly
nodejs
pip
tornado
virtualenv
mkdocs
mkdocs-material
pymdown-extensions
mkdocs-print-site-plugin
```
Выполнить установку этих пакетов:
```
apt-get update

apt-get install python3-dev python3-setuptools python-dev gcc python3-pip \
libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils rsync genisoimage wget gettext aptly -y -q

curl -sL https://deb.nodesource.com/setup_10.x | bash -

apt-get install -y nodejs

/usr/bin/python3 -m pip --no-cache-dir install 'pip==20.3.4' --force-reinstall

/usr/bin/python3 -m pip --no-cache-dir install 'tornado==5.1.1' 'virtualenv==15.1.0' 'mkdocs==1.1.2' \
'mkdocs-material==7.1.2' 'pymdown-extensions==8.0' 'mkdocs-print-site-plugin==1.0.0' --force-reinstall
```
4. Создать рабочий каталог, в который будут скопированы исходные тексты, с помощью команды:
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
## Сборка deb-пакетов
### veil-broker-backend
0. Установить переменные окружения:
```
export WORKSPACE="/tmp/veil-broker"
export PRJNAME="veil-broker-backend"
export DEB_ROOT="$WORKSPACE/devops/deb"
export VERSION="3.0.0"
```
1. Выполнить команды для сборки deb-пакета:
```
cd $WORKSPACE
sed -i "s:%%VER%%:$VERSION:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"

mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"
rsync -a backend/ "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app"

/usr/bin/python3 -m virtualenv ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env
cd ${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/app
${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/env/bin/python -m pip --no-cache-dir install -r requirements.txt
virtualenv --relocatable ../env

cd common
chmod +x compilemessages.sh
./compilemessages.sh en
./compilemessages.sh ru
cd ..
make -C "${DEB_ROOT}/${PRJNAME}"
```
### veil-broker-frontend
0. Установить переменные окружения:
```
export WORKSPACE="/tmp/veil-broker"
export PRJNAME="veil-broker-frontend"
export DEB_ROOT="$WORKSPACE/devops/deb"
export VERSION="3.0.0"
```
1. Выполнить команды для сборки deb-пакета:
```
cd $WORKSPACE
sed -i "s:%%VER%%:$VERSION:g" "$DEB_ROOT/$PRJNAME/root/DEBIAN/control"

npm cache clean --force
cd frontend
npm install --no-cache --unsafe-perm
npm run build -- --prod

mkdir -p "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"
cp -r ${WORKSPACE}/frontend/dist/frontend/* "${DEB_ROOT}/${PRJNAME}/root/opt/veil-vdi/www"
make -C ${DEB_ROOT}/${PRJNAME}
```
## Сборка iso-образа
0. Установить переменные окружения:
```
export WORKSPACE="/tmp/veil-broker"
export DEB_ROOT="$WORKSPACE/devops/deb"
export VERSION="3.0.0"
export DATE=$(date '+%Y%m%d%H%M%S')
export ISO_NAME="veil-broker-${VERSION}-${DATE}"
```
1. Выполнить команды для сборки iso-образа:
```
cd $WORKSPACE
wget http://dl.astralinux.ru/astra/stable/orel/repository/pool/main/a/ansible/ansible_2.7.7%2Bdfsg-1%2Bastra1_all.deb
rm -rf ~/.aptly
aptly repo create broker_iso
aptly repo add broker_iso ${DEB_ROOT}/veil-broker-backend/*.deb ${DEB_ROOT}/veil-broker-frontend/*.deb $WORKSPACE/ansible*.deb
aptly publish repo -skip-signing=true -distribution=smolensk broker_iso

mkdir -p $WORKSPACE/iso/repo
rsync -aq  ~/.aptly/public/pool $WORKSPACE/iso/repo/
rsync -aq  ~/.aptly/public/dists $WORKSPACE/iso/repo/

cp -r devops/ansible iso/ansible
rm -f iso/ansible/*.png iso/ansible/*.md iso/ansible/LICENSE
cp devops/installer/install.sh iso

genisoimage -o ./${ISO_NAME}.iso -V veil-broker -R -J ./iso
```
2. Установочный iso-образ VeiL Broker будет доступен в каталоге: `/tmp/veil-broker`