#!/bin/bash
# debug - bash vdi-deploy.sh 2>error.log

ROOT_DIR=/opt/veil-vdi
CONF_DIR=${ROOT_DIR}/devops/deb-config/vdi-backend/root/opt/veil-vdi/other
BACKEND_DIR=${ROOT_DIR}/app
FRONTEND_DIR=${ROOT_DIR}/frontend
WWW_DIR=${ROOT_DIR}/www
ENV_DIR=${ROOT_DIR}/env
OTHER_DIR=${ROOT_DIR}/other
SSL_DIR=${OTHER_DIR}/veil_ssl

mkdir ${OTHER_DIR}
mkdir ${BACKEND_DIR}
mkdir ${ENV_DIR}
mkdir ${SSL_DIR}
mkdir ${WWW_DIR}

# Переносим backend в app/
cp -r ${ROOT_DIR}/backend/* ${BACKEND_DIR}

echo "Install base packages"

sed -i s/us\./ru\./g /etc/apt/sources.list
apt-get update -y
apt-get install -y postgresql-server-dev-9.6 python3-dev python3-setuptools python-dev gcc python3-pip postgresql htop mc nginx libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils

echo "Installing additional packages"
apt-get install -y supervisor logrotate

echo "Installing node v.10 && npm"
curl -sL https://deb.nodesource.com/setup_10.x | bash
apt-get install -y nodejs

#------------------------------
echo "Setting up redis"
apt-get install -y redis-server
systemctl enable redis-server.service
# Сохраняем исходный конфиг
cp /etc/redis/redis.conf /etc/redis/redis.default
# Подкладываем наш из conf
cp ${CONF_DIR}/vdi.redis /etc/redis/redis.conf
systemctl restart redis-server

#------------------------------
echo "Setting up database"

# Сохраняем исходный конфиг
cp /etc/postgresql/9.6/main/postgresql.conf /etc/postgresql/9.6/main/postgresql.default
# Перекладываем наш из conf
cp ${CONF_DIR}/vdi.postgresql /etc/postgresql/9.6/main/postgresql.conf

# Добавляем возможность подключения с удаленного сервера к БД внутри vagrant
sed -i 's/peer/trust/g' /etc/postgresql/9.6/main/pg_hba.conf
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '0.0.0.0'/g" /etc/postgresql/9.6/main/postgresql.conf
echo 'host  vdi postgres  0.0.0.0/0  trust' >> /etc/postgresql/9.6/main/pg_hba.conf
systemctl restart postgresql

# Создаем БД
echo 'postgres:postgres' | chpasswd
sudo su postgres -c "psql -c \"ALTER ROLE postgres PASSWORD 'postgres';\" "
# На астре нету бездуховной кодировки en_US.UTF-8. Есть C.UTF-8
sudo su postgres -c "psql -c \"create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;\" "

#------------------------------
echo "Setting up vdi folder"
cd ${ROOT_DIR}

#------------------------------
echo "Setting up nginx"
cp ${CONF_DIR}/veil_ssl/veil_default.crt ${SSL_DIR}/veil_default.crt
cp ${CONF_DIR}/veil_ssl/veil_default.key ${SSL_DIR}/veil_default.key
cp ${CONF_DIR}/vdi.nginx /etc/nginx/conf.d/vdi_nginx.conf
rm /etc/nginx/sites-enabled/*
systemctl restart nginx

#------------------------------
echo "Setting up env"

export PYTHONPATH=${BACKEND_DIR}
export PIPENV_PIPFILE=${BACKEND_DIR}/Pipfile
/usr/bin/python3 -m pip install 'virtualenv<20.0.0' --force-reinstall  # На версии 20.0.0 перестал работать pipenv
/usr/bin/python3 -m pip install pipenv
/usr/local/bin/pipenv install

# Переносим установленное окружение в /opt/veil-vdi/env
export PIPENV_VERBOSITY=-1
cp -r $(/usr/local/bin/pipenv --venv)/* ${ENV_DIR}

#------------------------------
echo "Apply database migrations"
cd ${BACKEND_DIR}
/opt/veil-vdi/env/bin/alembic upgrade head

#------------------------------
echo "Setting up frontend"

cd ${FRONTEND_DIR}
rm -rf node_modules/ dist/
npm install --unsafe-perm
npm run build -- --prod
mkdir ${ROOT_DIR}/tmp
cp -r ${FRONTEND_DIR}/dist/frontend/* ${WWW_DIR}/
echo "Frontend compiled to /opt/veil-vdi/www"

#------------------------------
echo "Creating logs directory at /var/log/veil-vdi/"
mkdir /var/log/veil-vdi/

echo "Deploying configuration files for logrotate"

cp ${CONF_DIR}/tornado.logrotate /etc/logrotate.d/veil-vdi

echo "Deploying configuration files for supervisor"
cp /etc/supervisor/supervisord.conf /etc/supervisor/supervisord.default
cp ${CONF_DIR}/supervisord.conf /etc/supervisor/supervisord.conf
cp ${CONF_DIR}/tornado.supervisor ${OTHER_DIR}/tornado.supervisor
supervisorctl reload

echo "Vdi backend status:"
supervisorctl status

rm -rf ${ROOT_DIR}/devops
rm -rf ${ROOT_DIR}/backend
rm -rf ${ROOT_DIR}/tmp
rm -rf ${FRONTEND_DIR}

gpasswd -a www-data vagrant
chmod g+x www/
chown vagrant:vagrant ${WWW_DIR}/ -R
systemctl restart nginx
