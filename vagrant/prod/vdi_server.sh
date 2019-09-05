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
