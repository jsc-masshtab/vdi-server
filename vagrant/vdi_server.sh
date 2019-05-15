cd /vagrant/backend/vdi_server
echo "vdi_server: setting env..."
echo "export PIPENV_SKIP_LOCK=1" >> /home/vagrant/.bashrc
export PIPENV_SKIP_LOCK=1
pipenv install

echo "vdi_server: applying migrations..."
pipenv run mi apply

echo "vdi_server: prepare qcow image"
pipenv run python -m vdi.prepare

echo "vdi_server: starting server..."
pkill uvicorn
nohup pipenv run uvicorn vdi.app:app --host 0.0.0.0 --port 80 &