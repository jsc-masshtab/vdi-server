echo "Upgrade arch..."
pacman --noconfirm -Syu

echo "Installing packages..."
pacman --noconfirm -S --needed base-devel
pacman --noconfirm -S python-pip postgresql git
python -m pip install pipenv

cd /vagrant

if ! [ -x "$(command -v psql)" ]; then
  echo "Setting postgresql..."
  su postgres -c "initdb -D /var/lib/postgres/data"
  systemctl enable postgresql
  systemctl start postgresql
fi


sudo su postgres -c "psql -c \"drop database vdi;\" "
sudo su postgres -c "psql -c \"create database vdi;\" "


echo "Setting env..."
echo "export PIPENV_SKIP_LOCK=1" >> /home/vagrant/.bashrc
export PIPENV_SKIP_LOCK=1
pipenv install

echo "Applying migrations..."
pipenv run mi apply

echo "Running the server..."
pipenv run uvicorn vdi.app:app --host 0.0.0.0