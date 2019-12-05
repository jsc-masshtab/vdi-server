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
    start                start front and back with nohup
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
  echo "Update repository"
  git pull
  echo "Apply database migrations"
  cd $APP_DIR/backend
  pipenv run alembic upgrade head
}

start() {
  # TODO: tmux start for monitoring
  # TODO: supervisor start
  echo "Starting..."
  nohup pipenv run python $APP_DIR/backend/app.py &\
  cd $APP_DIR/frontend/
  rm -rf node_modules  # audit fix not working without this.
  npm audit fix  # npm i has some broken dependencies. npm audit fix works fine for 9
  nohup npm run ng serve -- --configuration=demo --host 0.0.0.0
  echo "Done!"
}

# parse argv
while test $# -ne 0; do
  arg=$1; shift
  case $arg in
    -h|--help) usage; exit ;;
    curr|current) current_commit; exit ;;
    update) setup_env; update; exit ;;
    start) setup_env; start; exit ;;
  esac
done

