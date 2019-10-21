echo "Install apt packages"

sudo sed -i s/us\./ru\./g /etc/apt/sources.list
sudo apt update -y
sudo apt install --no-install-recommends -y postgresql-server-dev-9.6 python3-dev gcc python3-pip postgresql htop mc nginx # Не нашел на астре пакеты ncdu и bmon

echo "Installing node v.10 && npm"
#sudo apt -y install curl dirmngr apt-transport-https lsb-release ca-certificates
curl -sL https://deb.nodesource.com/setup_10.x | sudo bash
sudo apt install -y nodejs

#------------------------------
echo "Setting up database"

sudo sed -i 's/peer/trust/g' /etc/postgresql/9.6/main/pg_hba.conf
sudo systemctl restart postgresql

echo 'postgres:postgres' | sudo chpasswd
sudo su postgres -c "psql -c \"ALTER ROLE postgres PASSWORD 'postgres';\" "
# На астре нету бездуховной кодировки en_US.UTF-8. Есть C.UTF-8
sudo su postgres -c "psql -c \"create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;\" "

#------------------------------
echo "Setting up vdi folder"

APP_DIR=/opt/veil-vdi
cd $APP_DIR

#------------------------------
echo "Setting up nginx"

sudo cp $APP_DIR/vagrant/dev/vdi_nginx.conf /etc/nginx/conf.d/vdi_nginx.conf
sudo rm /etc/nginx/sites-enabled/*
sudo systemctl restart nginx

#------------------------------
echo "Setting up env"

sudo python3.5 -m pip install pipenv
export PIPENV_PIPFILE=$APP_DIR/backend/Pipfile_future
pipenv install

#------------------------------
echo "Setting up backend"

nohup pipenv run python $APP_DIR/backend/vdi2/app.py & #nohup pipenv run vdi &

#------------------------------
echo "Setting up frontend"

cd $APP_DIR/frontend/
rm -rf node_modules
npm audit fix  # npm i has some broken dependencies. npm audit fix works fine for 9
npm run ng serve -- --host 0.0.0.0
