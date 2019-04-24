cd /vagrant/backend/auth_server
echo "auth_server: setting env..."
export PIPENV_SKIP_LOCK=1
pipenv install
nohup pipenv run python -m sanic main.app --host=0.0.0.0 --port=5000 &