# Astra Linux Orel 2.12
Для установки **VeiL Connect** с сервера **НИИ "Масштаб"** на **Astra Linux Orel 2.12** выполнить следующие команды:

```
sudo apt-get update && sudo apt-get install apt-transport-https wget -y
wget -qO - https://veil-update.mashtab.org/veil-repo-key.gpg | sudo apt-key add -
echo "deb https://veil-update.mashtab.org/veil-connect/linux/apt bionic main" | sudo tee /etc/apt/sources.list.d/veil-connect.list
sudo apt-get update && sudo apt-get install veil-connect -y
```