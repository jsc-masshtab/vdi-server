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
EOF
}

current_commit() {
  echo "Current commit: "
  git rev-parse --short HEAD
}

update() {
  echo "Update repository"
  git pull
  echo "Apply database migrations"
  cd $APP_DIR/backend/vdi2
  pipenv run alembic upgrade head
}

# parse argv
while test $# -ne 0; do
  arg=$1; shift
  case $arg in
    -h|--help) usage; exit ;;
    curr|current) current_commit; exit ;;
    update) update; exit ;;
  esac
done

