# Centos 7 / Centos 8
Для установки **VeiL Connect** с сервера **НИИ "Масштаб"** на **Centos 7 / Centos 8** выполнить следующие команды:

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