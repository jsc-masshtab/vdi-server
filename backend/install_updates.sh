#!/usr/bin/env bash

ROOT_DIRECTORY='/opt/veil-vdi'
BACKUP_PATH='/opt/backup/veil-vdi/'$(date +"%Y%m%d%H%M")

BACKEND_DIR=${ROOT_DIRECTORY}/app
FRONTEND_DIR=${ROOT_DIRECTORY}/www
ENV_DIR=${ROOT_DIRECTORY}/env
ALEMBIC_PATH=${ENV_DIR}/bin/alembic

#sudo apt-get --only-upgrade install atop

check_privileges(){
  if [ "$EUID" -ne 0 ]
    then echo "Please run as root"
    exit
  fi
}

show_expected_paths(){
  echo "Expected paths:"
  echo ${ROOT_DIRECTORY}
  echo ${BACKEND_DIR}
  echo ${FRONTEND_DIR}
  echo ${ENV_DIR}
  echo ${ALEMBIC_PATH}
  echo "${BACKUP_PATH}"
  echo "============================"
}

stop_services(){
  NGINX_STOP='/etc/init.d/nginx stop'
  BROKER_STOP='supervisorctl stop vdi-server-8888'
  echo "Stopping services..."
  echo "${NGINX_STOP}"
  ${NGINX_STOP}
  echo "${BROKER_STOP}"
  ${BROKER_STOP}
}

create_backup(){
  echo "Existing data backup path: ${BACKUP_PATH}"
  mkdir -p "${BACKUP_PATH}"
  echo "Copy existing files:"
  cp -rf "${ROOT_DIRECTORY}" "${BACKUP_PATH}"
}

get_updates(){
  apt-get update
  apt-get --only-upgrade install vdi-backend vdi-frontend
}

make_migrations(){
  echo "Running migrations..."
  export PYTHONPATH=${BACKEND_DIR}
  ${ALEMBIC_PATH} upgrade head
  echo "Migrations done."
}

start_services(){
  NGINX_START='/etc/init.d/nginx start'
  BROKER_START='supervisorctl start vdi-server-8888'
  echo "Starting services..."
  echo "${NGINX_START}"
  ${NGINX_START}
  echo "${BROKER_START}"
  ${BROKER_START}
}

run() {
  check_privileges;
  show_expected_paths;
  stop_services;
  create_backup;
  get_updates;
  make_migrations;
  start_services;
  echo "Done."
}

run;