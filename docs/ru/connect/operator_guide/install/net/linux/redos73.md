# RedOS 7.3

Для установки **VeiL Connect** с сервера **НИИ "Масштаб"** на **RedOS 7.3** выполнить следующие команды:

`tee /etc/yum.repos.d/veil-connect.repo <<EOF`  
`[veil-connect]`  
`name=VeiL Connect repository`  
`baseurl=https://veil-update.mashtab.org/veil-connect/linux/yum/redos7.3/\$basearch`  
`gpgcheck=1`  
`gpgkey=https://veil-update.mashtab.org/veil-connect/linux/yum/RPM-GPG-KEY-veil-connect`  
`enabled=1`  
`EOF`  
`dnf install veil-connect -y`
