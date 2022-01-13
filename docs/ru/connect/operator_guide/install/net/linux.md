# Установка  на операционную систему Linux

Для автоматической установки VeiL Connect на любую из поддерживаемых ОС семейства Linux необходимо выполнить следующие действия:

- запустить терминал;

-  в терминале запустить универсальный установочный скрипт путем выполнения следующих команд:
```bash
wget https://veil-update.mashtab.org/veil-connect/linux/veil-connect-linux-installer.sh
sudo bash veil-connect-linux-installer.sh
```

- после выполнения команд необходимо выбрать ОС из списка. В случае, если список ОС откроется в графической оболочке необходимо выбрать ОС и нажать кнопку "ОК". Если список откроется текстом в терминале необходимо набрать номер ОС из списка и нажать Enter. 

В случае если для установки Veil Connect не подходит использование универсального установочного скрипта, выполняйте нижеследующие команды для каждой из поддерживаемых ОС.

### Debian 9 (Stretch)
Выполнить команды в терминале:
```bash
sudo apt-get update && sudo apt-get install apt-transport-https wget lsb-release -y
wget -qO - https://veil-update.mashtab.org/veil-repo-key.gpg | sudo apt-key add -
# add stretch-backports repo (for freerdp 2.0)
echo "deb http://deb.debian.org/debian stretch-backports main" | sudo tee /etc/apt/sources.list.d/stretch-backports.list
echo "deb https://veil-update.mashtab.org/veil-connect/linux/apt $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/veil-connect.list
sudo apt-get update && sudo apt-get install veil-connect -y
sudo rm -f /etc/apt/sources.list.d/stretch-backports.list && sudo apt-get update
```
### Debian 10 (Buster) / Ubuntu 16.04 (Xenial) / Ubuntu 18.04 (Bionic) / Ubuntu 20.04 (Focal)

Выполнить команды в терминале:
```bash
sudo apt-get update && sudo apt-get install apt-transport-https wget lsb-release -y
wget -qO - https://veil-update.mashtab.org/veil-repo-key.gpg | sudo apt-key add -
echo "deb https://veil-update.mashtab.org/veil-connect/linux/apt $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/veil-connect.list
sudo apt-get update && sudo apt-get install veil-connect -y
```
### Centos 7 / Centos 8
Выполнить команды в терминале:
```bash
sudo tee /etc/yum.repos.d/veil-connect.repo <<EOF
[veil-connect]
name=VeiL Connect repository
baseurl=https://veil-update.mashtab.org/veil-connect/linux/yum/el\$releasever/\$basearch
gpgcheck=1
gpgkey=https://veil-update.mashtab.org/veil-connect/linux/yum/RPM-GPG-KEY-veil-connect
enabled=1
EOF
 
sudo yum install veil-connect -y
```
### Astra Linux Orel 2.12
Выполнить команды в терминале:
```bash
sudo apt-get update && sudo apt-get install apt-transport-https wget -y
wget -qO - https://veil-update.mashtab.org/veil-repo-key.gpg | sudo apt-key add -
echo "deb https://veil-update.mashtab.org/veil-connect/linux/apt bionic main" | sudo tee /etc/apt/sources.list.d/veil-connect.list
sudo apt-get update && sudo apt-get install veil-connect -y
```
### Astra Linux Smolensk 1.6
1. Подключить iso-образ основного диска **Astra Linux Smolensk 1.6**, выполнить команды для копирования deb-пакетов в систему:
```bash
sudo mount /media/cdrom
sudo mkdir /opt/main
sudo cp -r /media/cdrom/pool /media/cdrom/dists /opt/main/
sudo umount /media/cdrom
```
2. Подключить iso-образ devel-диска **Astra Linux Smolensk 1.6**, выполнить команды для копирования deb-пакетов в систему:
```bash
sudo mount /media/cdrom
sudo mkdir /opt/devel
sudo cp -r /media/cdrom/pool /media/cdrom/dists /opt/devel/
sudo umount /media/cdrom
```
3. Настроить локальный apt-репозиторий, привести файл **/etc/apt/sources.list** к виду:
```bash
deb file:///opt/main smolensk contrib main non-free
deb file:///opt/devel smolensk contrib main non-free
```
4. Обновить списки пакетов командой:
```bash
sudo apt-get update
```
5. Открыть в браузере адрес: https://veil-update.mashtab.org/veil-connect/linux/apt/pool/main/v/veil-connect/ и загрузить deb-пакет последней версии, в названии которого присутствует ~stretch (например veil-connect_1.4.1~stretch_amd64.deb).
6. Перейти в каталог, в который был загружен deb-пакет на предыдущем шаге и выполнить команду для установки deb-пакета:
```bash
sudo apt-get install ./veil-connect*stretch*.deb -y
```
### Alt Linux 9

Выполнить команды в терминале:
```bash
apt-get update && apt-get install wget -y
wget https://veil-update.mashtab.org/veil-connect/linux/apt-rpm/x86_64/RPMS.alt9/veil-connect-latest.rpm
apt-get install ./veil-connect-latest.rpm -y
rm -f veil-connect-latest.rpm
```

### RedOS 7.2

Выполнить команды в терминале:
```bash
tee /etc/yum.repos.d/veil-connect.repo <<EOF
[veil-connect]
name=VeiL Connect repository
baseurl=https://veil-update.mashtab.org/veil-connect/linux/yum/el7/\$basearch
gpgcheck=1
gpgkey=https://veil-update.mashtab.org/veil-connect/linux/yum/RPM-GPG-KEY-veil-connect
enabled=1
EOF
yum install veil-connect freerdp-libs -y
```

### RedOS 7.3

Выполнить команды в терминале:
```bash
tee /etc/yum.repos.d/veil-connect.repo <<EOF
[veil-connect]
name=VeiL Connect repository
baseurl=https://veil-update.mashtab.org/veil-connect/linux/yum/redos7.3/\$basearch
gpgcheck=1
gpgkey=https://veil-update.mashtab.org/veil-connect/linux/yum/RPM-GPG-KEY-veil-connect
enabled=1
EOF
dnf install veil-connect -y
```