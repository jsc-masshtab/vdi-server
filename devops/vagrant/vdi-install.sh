#!/bin/bash
sed -i s#us\\.#ru\\.#g /etc/apt/sources.list

apt update -y

apt install -y gnupg2
wget -qO - http://192.168.11.118/veil_qa.key | sudo apt-key add -
echo 'deb http://192.168.11.118/vdi veil main' | sudo tee /etc/apt/sources.list.d/vdi.list

apt update -y

apt install -y mc vdi-backend

# apt install -y gdebi mc

# wget http://192.168.11.118/vdi/pool/main/v/vdi-backend/vdi-backend_1.2.3-28_amd64.deb
# wget http://192.168.11.118/vdi/pool/main/v/vdi-frontend/vdi-frontend_1.2.3-73_amd64.deb
# 
# gdebi vdi-frontend*.deb
# gdebi vdi-backend*.deb