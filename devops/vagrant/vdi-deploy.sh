#!/bin/bash

echo "Install apt-get packages"

sed -i s/us\./ru\./g /etc/apt/sources.list
apt-get update -y
apt-get install --no-install-recommends -y postgresql-server-dev-9.6 python3-dev gcc python3-pip postgresql htop mc nginx # Не нашел на астре пакеты ncdu и bmon
apt-get install -y libsasl2-dev python-dev libldap2-dev libssl-dev

echo "Installing node v.10 && npm"
curl -sL https://deb.nodesource.com/setup_10.x | bash
apt-get install -y nodejs

echo "Installing additional packages"
apt-get install -y supervisor logrotate


#------------------------------
echo "Setting up database"

sed -i 's/peer/trust/g' /etc/postgresql/9.6/main/pg_hba.conf
systemctl restart postgresql

echo 'postgres:postgres' | chpasswd
sudo su postgres -c "psql -c \"ALTER ROLE postgres PASSWORD 'postgres';\" "
# На астре нету бездуховной кодировки en_US.UTF-8. Есть C.UTF-8
sudo su postgres -c "psql -c \"create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;\" "


#------------------------------
echo "Setting up vdi folder"

APP_DIR=/vagrant

cd $APP_DIR


#------------------------------
echo "Setting up nginx"

cp $APP_DIR/devops/conf/vdi_nginx.conf /etc/nginx/conf.d/vdi_nginx.conf
rm /etc/nginx/sites-enabled/*
systemctl restart nginx


#------------------------------
echo "Setting up env"

python3.5 -m pip install setuptools 
python3.5 -m pip install pipenv
export PYTHONPATH=$APP_DIR/backend
export PIPENV_PIPFILE=$APP_DIR/backend/Pipfile
pipenv install


#------------------------------
echo "Apply database migrations"

cd $APP_DIR/backend
pipenv run alembic upgrade head


#------------------------------
echo "Setting up frontend"

cd $APP_DIR/frontend/
rm -rf node_modules/
rm -rf dist/
npm install --unsafe-perm
npm run build -- --prod
echo "Frontend compiled to /vagrant/frontend/dist/frontend/"


#------------------------------
echo "Creating logs directory at /var/log/veil-vdi/"
mkdir /var/log/veil-vdi/

echo "Deploying configuration files for logrotate"

cp $APP_DIR/devops/conf/veil-vdi /etc/logrotate.d/veil-vdi

echo "Deploying configuration files for supervisor"

rm /etc/supervisor/supervisord.conf
cp $APP_DIR/devops/conf/supervisord.conf /etc/supervisor/supervisord.conf
supervisorctl reload

echo "Vdi backend status:"
supervisorctl status
