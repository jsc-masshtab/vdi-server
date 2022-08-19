# AlterOS 7.x
Для установки **VeiL Connect** с сервера **НИИ "Масштаб"** на **AlterOS 7.x** выполнить следующие команды:

`sudo tee /etc/yum.repos.d/veil-connect.repo <<EOF`  
`[veil-connect]`  
`name=VeiL Connect repository`  
`baseurl=https://veil-update.mashtab.org/veil-connect/linux/yum/alteros7/\$basearch`  
`gpgcheck=1`  
`gpgkey=https://veil-update.mashtab.org/veil-connect/linux/yum/RPM-GPG-KEY-veil-connect`  
`enabled=1`  
`EOF`

`sudo yum erase -y freerdp-libs`

`sudo yum install -y http://mirror.centos.org/centos/7/os/x86_64/Packages/libwinpr-2.1.1-2.el7.x86_64.rpm`

`sudo yum install -y http://mirror.centos.org/centos/7/os/x86_64/Packages/freerdp-libs-2.1.1-2.el7.x86_64.rpm`

`sudo yum install -y https://download-ib01.fedoraproject.org/pub/epel/7/x86_64/Packages/h/hiredis-0.12.1-2.el7.x86_64.rpm`

`sudo yum install veil-connect -y`
