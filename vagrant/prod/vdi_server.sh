cd ../../backend

sudo python3.5 -m pip install pipenv

echo "vdi_server: setting env..."
export PIPENV_SKIP_LOCK=1
export PIPENV_PIPFILE=Pipfile
pipenv install

# install special starlette
pipenv run  python3.5 -m pip install git+https://github.com/em92/starlette
pipenv graph

echo "vdi_server: applying migrations..."
pipenv run python3.5 mi-pkg/mi/main.py apply

echo "vdi_server: starting server..."
pkill python
pipenv run python3.5 main.py &


