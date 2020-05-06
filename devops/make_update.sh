#!/usr/bin/env bash

CURRENT_DATE=$(date +"%Y%m%d%H%M")
ROOT_DIRECTORY='tmp'${CURRENT_DATE};
BACKEND_DIR=${ROOT_DIRECTORY}/app/
FRONTEND_DIR=${ROOT_DIRECTORY}/www/
CONF_DIR=${ROOT_DIRECTORY}/other/
ENV_DIR=${ROOT_DIRECTORY}/env/


usage() {
  cat <<-EOF
  Usage: deploy [options] [command]
  Options:
    -h, --help             show help information
  Commands:
    -n                     generate new update from vagrant in directory
EOF
}

prepare_folders(){
  echo "Setting up folder structure for feature updates..."

  mkdir -p -v "${ROOT_DIRECTORY}"
  mkdir -p -v "${BACKEND_DIR}"
  mkdir -p -v "${FRONTEND_DIR}"
  mkdir -p -v "${CONF_DIR}"
  mkdir -p -v "${ENV_DIR}"
}

get_frontend_dir(){
  echo "Getting frontend staticfiles from Vagrant..."
  scp -r vagrant@192.168.20.112:/opt/veil-vdi/www/* "${FRONTEND_DIR}"
}

get_configurations(){
  echo "Getting configuration files from Vagrant..."
  rsync -rv --exclude={license} vagrant@192.168.20.112:/opt/veil-vdi/other/ ${CONF_DIR}
}

get_backend(){
  echo "Getting backend files from Vagrant..."
  rsync -rv --exclude={*.pyc,.idea,.pytest_cache,__pycache__,.coveragerc,.python-version,tests} vagrant@192.168.20.112:/opt/veil-vdi/app/ "${BACKEND_DIR}"
}

get_env(){
  echo "Getting env from Vagrant..."
  rsync -rv vagrant@192.168.20.112:/opt/veil-vdi/env/ ${ENV_DIR}
}

compress_results(){
  echo "Compressing results..."
  tar -cvzf "${ROOT_DIRECTORY}${currentDate}.tar.gz" ${ROOT_DIRECTORY}
}

remove_tmp(){
  echo "Removing temporary directory ${ROOT_DIRECTORY}"
  rm -rf "${ROOT_DIRECTORY}"
}

run() {
  prepare_folders;
  get_frontend_dir;
  get_configurations;
  get_backend;
  get_env;
  compress_results;
  remove_tmp;
  echo "Done."
}

run;
