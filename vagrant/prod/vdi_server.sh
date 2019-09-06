cd ../../backend

echo "vdi_server: setting env..."
echo "export PIPENV_SKIP_LOCK=1" >> /home/vagrant/.bashrc
export PIPENV_SKIP_LOCK=1
#export PIPENV_PIPFILE=/vagrant/vagrant/prod/Pipfile
pipenv install

echo "vdi_server: applying migrations..."
pipenv run python mi-pkg/mi/main.py

echo "vdi_server: starting server..."
pkill python
nohup pipenv run python main.py &


