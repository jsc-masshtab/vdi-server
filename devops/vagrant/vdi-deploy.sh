#!/bin/bash
APP_DIR=/opt/veil-vdi

echo "Install base packages"

sed -i s/us\./ru\./g /etc/apt/sources.list
apt-get update -y
apt-get install -y postgresql-server-dev-9.6 python3-dev python3-setuptools python-dev gcc python3-pip postgresql htop mc nginx libsasl2-dev libldap2-dev libssl-dev

echo "Installing additional packages"
apt-get install -y supervisor logrotate

echo "Installing node v.10 && npm"
curl -sL https://deb.nodesource.com/setup_10.x | bash
apt-get install -y nodejs

#------------------------------
echo "Setting up redis"

apt-get install -y redis-server
systemctl enable redis-server.service
echo 'requirepass 4NZ7GpHn4IlshPhb' >> /etc/redis/redis.conf
systemctl restart redis-server

#------------------------------
echo "Setting up database"

cp $APP_DIR/devops/conf/vdi.postgresql /etc/postgresql/9.6/main/postgresql.conf
sed -i 's/peer/trust/g' /etc/postgresql/9.6/main/pg_hba.conf
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '192.168.20.112,127.0.0.1'/g" /etc/postgresql/9.6/main/postgresql.conf
echo 'host  vdi postgres  0.0.0.0/0  trust' >> /etc/postgresql/9.6/main/pg_hba.conf
systemctl restart postgresql

echo 'postgres:postgres' | chpasswd
sudo su postgres -c "psql -c \"ALTER ROLE postgres PASSWORD 'postgres';\" "
# На астре нету бездуховной кодировки en_US.UTF-8. Есть C.UTF-8
sudo su postgres -c "psql -c \"create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;\" "

#------------------------------
echo "Setting up vdi folder"
cd $APP_DIR

#------------------------------
echo "Setting up nginx"

cp $APP_DIR/devops/conf/vdi.nginx /etc/nginx/conf.d/vdi_nginx.conf
rm /etc/nginx/sites-enabled/*
systemctl restart nginx

#------------------------------
echo "Setting up env"

export PYTHONPATH=$APP_DIR/backend
export PIPENV_PIPFILE=$APP_DIR/backend/Pipfile
/usr/bin/python3 -m pip install 'virtualenv<20.0.0' --force-reinstall  # На версии 20.0.0 перестал работать pipenv
/usr/bin/python3 -m pip install pipenv
pipenv install

#------------------------------
echo "Apply database migrations"

cd $APP_DIR/backend
pipenv run alembic upgrade head

#------------------------------
echo "Setting up frontend"

cd $APP_DIR/frontend/
rm -rf node_modules/ dist/
npm install --unsafe-perm
npm run build -- --prod

echo "Frontend compiled to /opt/veil-vdi/frontend/dist/frontend/"

#------------------------------
echo "Creating logs directory at /var/log/veil-vdi/"
mkdir /var/log/veil-vdi/

echo "Deploying configuration files for logrotate"

cp $APP_DIR/devops/conf/tornado.logrotate /etc/logrotate.d/veil-vdi

echo "Deploying configuration files for supervisor"

rm /etc/supervisor/supervisord.conf
cp $APP_DIR/devops/conf/supervisord.conf /etc/supervisor/supervisord.conf
supervisorctl reload

echo "Vdi backend status:"
supervisorctl status
