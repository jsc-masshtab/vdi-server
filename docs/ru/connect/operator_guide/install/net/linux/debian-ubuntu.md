# Debian 10 / Ubuntu

Для установки **VeiL Connect** с сервера **НИИ "Масштаб"** на **Debian 10 (Buster) / Ubuntu 16.04 (Xenial) / Ubuntu 18.04 (Bionic) / Ubuntu 20.04 (Focal) / Ubuntu 22.04 (Jammy)** выполнить следующие команды:

`sudo apt-get update && sudo apt-get install apt-transport-https wget lsb-release gnupg -y`  
`sudo wget -O /usr/share/keyrings/veil-repo-key.gpg https://veil-update.mashtab.org/veil-repo-key.gpg`  
`echo "deb [arch=amd64 signed-by=/usr/share/keyrings/veil-repo-key.gpg] https://veil-update.mashtab.org/veil-connect/linux/apt $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/veil-connect.list`  
`sudo apt-get update && sudo apt-get install veil-connect -y`  
