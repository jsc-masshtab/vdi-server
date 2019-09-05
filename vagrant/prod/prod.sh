echo "Install apt packages"

sudo sed -i s/us\./ru\./g /etc/apt/sources.list
sudo apt update -y
sudo apt install --no-install-recommends -y postgresql-server-dev-11 python3-dev gcc python3-pip postgresql htop ncdu mc bmon

#------------------------------
echo "Setup database"

sudo sed -i 's/peer/trust/g' /etc/postgresql/11/main/pg_hba.conf
sudo systemctl restart postgresql

echo 'postgres:postgres' | sudo chpasswd
sudo su postgres -c "psql -c \"ALTER ROLE postgres PASSWORD 'postgres';\" "
sudo su postgres -c "psql -c \"create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;\" "

sudo python3 -m pip install pipenv

#------------------------------
echo "Setup vdi server"

cd /vagrant/backend

echo "vdi_server: setting env..."
echo "export PIPENV_SKIP_LOCK=1" >> /home/vagrant/.bashrc
export PIPENV_SKIP_LOCK=1
export PIPENV_PIPFILE=/vagrant/vagrant/prod/Pipfile
pipenv install

echo "vdi_server: applying migrations..."
pipenv run mi apply

echo "vdi_server: starting server..."
nohup pipenv run vdi &

#------------------------------
echo "Setup frontend"

cd /vagrant/frontend/
sudo snap install node --channel 11/stable --classic
rm -rf node_modules
/snap/bin/npm install

# Somehow doesn't work with nohup... Therefore, should be the last script to execute
/snap/bin/npm run ng serve -- --host 0.0.0.0