#!/bin/bash

APP_DIR=/opt/veil-vdi/frontend
cd $APP_DIR || exit

usage() {
  cat <<-EOF
  Usage: sh /opt/veil-vdi/entrypoint.sh [options]
  Options:
    -h, --help           output help information
    -dev, --development           install dependencies and run live angular server
    -prod, --production           clean install dependenciec and build angular with production arg
EOF
}

dev() {
  echo "Install dependencies and run live Angular server"
  echo "Directory is:";
  pwd;
  echo "Removing old dist and node_modules:"
  rm -rf node_modules dist;
  echo "Installing dependencies via npm:"
  npm install --unsafe-perm;
  echo "Running angular-live:"
  npm start -- -c=docker --host=0.0.0.0
}

prod() {
  echo "Clean install dependencies and build Angular with production arg";
  echo "Directory is:"
  pwd;
  echo "Removing old dist and node_modules:"
  rm -rf node_modules dist;
  echo "Installing dependencies via npm:"
  npm install --unsafe-perm;
  echo "Building code:"
  npm run build -- --prod
  echo "Code compilation completed. Files are in: frontend/dist/frontend"
}

# parse argv
while test $# -ne 0; do
  arg=$1; shift
  case $arg in
    -h|--help) usage; exit ;;
    -dev|--development) dev; exit ;;
    -prod|--production) prod; exit ;;
  esac
done

