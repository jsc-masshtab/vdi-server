# Debian 9 (Stretch)
Для установки **VeiL Connect** с сервера **НИИ "Масштаб"** на **Debian 9** выполнить следующие команды:

```
sudo apt-get update && sudo apt-get install apt-transport-https wget lsb-release -y
wget -qO - https://veil-update.mashtab.org/veil-repo-key.gpg | sudo apt-key add -
# add stretch-backports repo (for freerdp 2.0)
echo "deb http://deb.debian.org/debian stretch-backports main" | sudo tee /etc/apt/sources.list.d/stretch-backports.list
echo "deb https://veil-update.mashtab.org/veil-connect/linux/apt $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/veil-connect.list
sudo apt-get update && sudo apt-get install veil-connect -y
sudo rm -f /etc/apt/sources.list.d/stretch-backports.list && sudo apt-get update
```