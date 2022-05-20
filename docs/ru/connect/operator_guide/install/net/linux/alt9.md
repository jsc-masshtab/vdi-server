# Alt Linux 9

Для установки **VeiL Connect** с сервера **НИИ "Масштаб"** на **Alt Linux 9** выполнить следующие команды:

`apt-get update && apt-get install wget -y`

`wget https://veil-update.mashtab.org/veil-connect/linux/apt-rpm/x86_64/RPMS.alt9/veil-connect-latest.rpm`

`apt-get install ./veil-connect-latest.rpm -y`

`rm -f veil-connect-latest.rpm`  
