#!/usr/bin/env bash

APP_DIR=/opt/veil-vdi
cd $APP_DIR

usage() {
  cat <<-EOF
  Usage: deploy [options] [command]
  Options:
    -h, --help           output help information
  Commands:
    update               update deploy to the latest release / apply db migrations
    curr[ent]            output current release commit
    start                start front and back with supervisorctl
    stop                stop front and back with supervisorctl
EOF
}

setup_env() {
  echo "Setting up env"
  export PYTHONPATH=$APP_DIR/backend
}

current_commit() {
  echo "Current commit: "
  git rev-parse --short HEAD
}

update() {
  echo "Update from repository"
  git pull
  echo "Stopping VDI Tornado..."
  supervisorctl stop vdi-server-8888
  echo "Apply database migrations"
  cd $APP_DIR/backend
  pipenv run alembic upgrade head
  echo "Starting VDI Tornado..."
  supervisorctl start vdi-server-8888
  echo "Preparing frontend..."
  cd $APP_DIR/frontend/
  echo "Removing old node_modules/..."
  rm -rf node_modules
  echo "Removing old dis/..."
  rm -rf dist/
  echo "Installing NODE dependencies..."
  npm install --unsafe-perm
  echo "Compiling Angular"
   npm run build -- --prod
#  npm run build
  echo "Restarting nginx..."
  /etc/init.d/nginx restart
  echo "Done!"
}

start() {
  echo "Starting supervisor vdi-server-8888..."
  supervisorctl start vdi-server-8888
  echo "Preparing frontend..."
  cd $APP_DIR/frontend/
  echo "Removing old node_modules/..."
  rm -rf node_modules
  echo "Removing old dis/..."
  rm -rf dist/
  echo "Installing NODE dependencies..."
  npm install --unsafe-perm
  echo "Compiling Angular"
   npm run build -- --prod
#  npm run build
  echo "Restarting nginx..."
  /etc/init.d/nginx restart
  echo "Done!"
}

stop() {
  echo "Stopping tornado"
  supervisorctl stop vdi-server-8888
}

# parse argv
while test $# -ne 0; do
  arg=$1; shift
  case $arg in
    -h|--help) usage; exit ;;
    curr|current) current_commit; exit ;;
    update) setup_env; update; exit ;;
    start) setup_env; start; exit ;;
    stop) setup_env; stop; exit ;;
  esac
done

