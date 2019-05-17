cd /vagrant/backend/auth_server
echo "auth_server: setting env..."
export PIPENV_SKIP_LOCK=1
pipenv install
pkill sanic_server
nohup pipenv run sanic_server main.app --host=0.0.0.0 --port=5000 &