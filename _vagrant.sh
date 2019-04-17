echo "Upgrade arch..."
pacman --noconfirm -Syu

echo "Installing packages..."
pacman --noconfirm -S --needed base-devel
pacman --noconfirm -S python-pip postgresql git nodejs npm

python -m pip install pipenv

cd /vagrant/backend/vdi_server
pkill uvicorn

# FIXME: rm -rf /var/lib/postgres/data
systemctl stop postgresql
echo "Setting postgresql..."
su postgres -c "initdb -D /var/lib/postgres/data"
systemctl enable postgresql
systemctl start postgresql

sudo su postgres -c "psql -c \"drop database vdi;\" "
sudo su postgres -c "psql -c \"create database vdi;\" "


echo "Setting env..."
echo "export PIPENV_SKIP_LOCK=1" >> /home/vagrant/.bashrc
export PIPENV_SKIP_LOCK=1
pipenv install

echo "Applying migrations..."
pipenv run mi apply

echo "Prepare qcow image"
pipenv run python -m vdi.prepare

echo "Running the API server..."
nohup pipenv run uvicorn vdi.app:app --host 0.0.0.0 --port 80 &


echo "Running the auth server..."
cd /vagrant/backend/auth_server
pipenv install
nohup pipenv run python -m sanic main.app --host=0.0.0.0 --port=5000 --workers=4 &


echo "Running the frontend server..."
cd /vagrant/frontend
rm -rf /vagrant/frontend/node_modules
npm install
nohup npm run ng serve -- --host 0.0.0.0 &

echo "Setup finished"