# Установка VeiL Connect
!!! note "Примечание"
    В окне существует возможность отменить процесс установки, нажав кнопку **Отменить**.

## Установка с CD/DVD

### Установка на ОС Linux
- вставить компакт-диск в дисковод CD/DVD-ROM;

- авторизоваться в системе с правами суперпользователя, имеющего
возможность установки пакетов (пользователь должен состоять в группе *sudo*);

- в зависимости от ОС и графической оболочки открыть **Менеджер файлов**
(**File Manager** или **Files**, **терминал Fly**, т.д.);

- открыть содержимое носителя;

!!! example "ОС **Astra Linux Special Edition** и **Astra Linux Common Edition**"
    открыть **Компьютер** -> **Накопители** -> в открывшемся окне 
    выбрать в корневой директории носителя файл **veil_connect-X.X.X-linux.tar** 
    (где Х.X.X – номер сборки Veil Connect).

- скопировать файл в домашний каталог пользователя и распаковать архив;
    
- выполнить установку Veil Connect;

!!! example "ОС **Astra Linux Special Edition** и **Astra Linux Common Edition**"
    1. запустить установку Veil Connect двойным нажатием правой кнопки мыши на 
    исполняемый файл **veil-connect-linux-installer.sh**;
    1. дождаться появления меню выбора операционной системы;
    1. в строке приглашения ввести номер, соответствующий выбранной ОС и
    нажать **Enter**.
      
!!! note "Примечание"
    Во время установки система может запросить пароль для получения привилегий *sudo*, 
    после ввода которого в отдельном окне будет выполнено обновление системы. 
    После обновления начнется установка Veil Connect вместе с необходимыми для работы пакетами.

### Установка на ОС Windows 
- вставить компакт-диск в дисковод CD/DVD-ROM;

- запустить менеджер файлов и перейти в корневую директорию носителя;

- запустить инсталляционный файл **Veil_connect_installer_Х.X.X.exe** (где Х.X.X – номер сборки Veil Connect).

## Установка по сети

### Windows 7 / 8 / 10 / 2008 R2 / 2012 / 2016
1. Открыть в браузере адрес: https://veil-update.mashtab.org/veil-connect/windows/latest.
2. Загрузить установочный exe-файл требуемой разрядности (x64 или x32).
3. Запустить установку от имени Администратора, следовать подсказкам установщика.
### Linux (универсальный установочный скрипт)
Выполнить команды в терминале:
```
wget https://veil-update.mashtab.org/veil-connect/linux/veil-connect-linux-installer.sh
sudo bash veil-connect-linux-installer.sh
```
### Debian 9 (Stretch)
Выполнить команды в терминале:
```
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
```
sudo apt-get update && sudo apt-get install apt-transport-https wget lsb-release -y
wget -qO - https://veil-update.mashtab.org/veil-repo-key.gpg | sudo apt-key add -
echo "deb https://veil-update.mashtab.org/veil-connect/linux/apt $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/veil-connect.list
sudo apt-get update && sudo apt-get install veil-connect -y
```
### Centos 7 / Centos 8
Выполнить команды в терминале:
```
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
```
sudo apt-get update && sudo apt-get install apt-transport-https wget -y
wget -qO - https://veil-update.mashtab.org/veil-repo-key.gpg | sudo apt-key add -
echo "deb https://veil-update.mashtab.org/veil-connect/linux/apt bionic main" | sudo tee /etc/apt/sources.list.d/veil-connect.list
sudo apt-get update && sudo apt-get install veil-connect -y
```
### Astra Linux Smolensk 1.6
1. Подключить iso-образ основного диска Astra Linux Smolensk 1.6, выполнить команды для копирования deb-пакетов в систему:
```
sudo mount /media/cdrom
sudo mkdir /opt/main
sudo cp -r /media/cdrom/pool /media/cdrom/dists /opt/main/
sudo umount /media/cdrom
```
2. Подключить iso-образ devel-диска Astra Linux Smolensk 1.6, выполнить команды для копирования deb-пакетов в систему:
```
sudo mount /media/cdrom
sudo mkdir /opt/devel
sudo cp -r /media/cdrom/pool /media/cdrom/dists /opt/devel/
sudo umount /media/cdrom
```
3. Настроить локальный apt-репозиторий, привести файл /etc/apt/sources.list к виду:
```
deb file:///opt/main smolensk contrib main non-free
deb file:///opt/devel smolensk contrib main non-free
```
4. Обновить списки пакетов командой:
```
sudo apt-get update
```
5. Открыть в браузере адрес: https://veil-update.mashtab.org/veil-connect/linux/apt/pool/main/v/veil-connect/ и загрузить deb-пакет последней версии, в названии которого присутствует ~stretch (например veil-connect_1.4.1~stretch_amd64.deb).
6. Перейти в каталог, в который был загружен deb-пакет на предыдущем шаге и выполнить команду для установки deb-пакета:
```
sudo apt-get install ./veil-connect*stretch*.deb -y
```
