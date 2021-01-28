#!/bin/bash

# check installed packages
if !(dpkg -s veil-broker-backend 1> /dev/null 2>&1); then
    echo "Error: veil-broker packages is not installed!" && exit 1
fi

# set variables
UPGRADE_DIR="/home/user/upgrade"
REPO_URL="veil-update.mashtab.org"
REPO_NAME="veil-broker"

echo "VeiL Broker upgrade started"

echo "Select upgrade type:"
echo "
    1. by apt (access to the $REPO_URL is required)
    2. local (veil-broker deb packages in $UPGRADE_DIR is required)
"
echo "Type is:"
read TYPE

case $TYPE in
    1)
        if !(ping -q -w 1 -c 1 $REPO_URL 1> /dev/null 2>&1); then
            echo "Error: $REPO_URL is not reachable" && exit 1
        fi
        wget -qO - https://$REPO_URL/veil-repo-key.gpg | apt-key add -
        echo "deb https://$REPO_URL/$REPO_NAME veil main" > /etc/apt/sources.list.d/vdi.list
        apt-get update
        ;;
    2)
        if !(ls $UPGRADE_DIR/veil-broker*.deb 1> /dev/null 2>&1); then
            echo "Error: deb-packages do not exist in $UPGRADE_DIR !" && exit 1
        fi
        ;;
    *)
        echo "Error: Empty type!" && exit 1 ;;
esac

# stop services
if ls /etc/systemd/system/vdi*.service 1> /dev/null 2>&1 ; then
    service vdi-pool_worker stop
    service vdi-web stop
    service vdi-ws_listener stop
else
    supervisorctl stop vdi-pool_worker
    supervisorctl stop vdi-server-8888
    supervisorctl stop vdi-ws_listener_worker
fi

# upgrade packages
case $TYPE in
    1)
        apt-get install veil-broker-backend veil-broker-frontend -y
        apt-get -f -y install
        ;;
    2)
        cd $UPGRADE_DIR
        apt-get install ./veil-broker-*.deb -y
        apt-get -f -y install
        ;;
esac

# applying migrations
export PYTHONPATH=/opt/veil-vdi/app
cd /opt/veil-vdi/app/common/migrations
/opt/veil-vdi/env/bin/alembic upgrade head

# start services
if ls /etc/systemd/system/vdi*.service 1> /dev/null 2>&1 ; then
    service vdi-pool_worker start
    service vdi-web start
    service vdi-ws_listener start
else
    supervisorctl start vdi-pool_worker
    supervisorctl start vdi-server-8888
    supervisorctl start vdi-ws_listener_worker
fi

# restart web-server
if service apache2 status 1> /dev/null 2>&1 ; then
    service apache2 restart
else
    service nginx restart
fi