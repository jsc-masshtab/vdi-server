#!/bin/bash

APP_DIR=/opt/veil-vdi/conf
cd $APP_DIR || exit
echo "Stopping nginx..."
/etc/init.d/nginx stop
echo "Removing default config file..."
rm /etc/nginx/conf.d/default.conf
echo "Copy local config to nginx default dir"
cp vdi_nginx.conf /etc/nginx/conf.d/default.conf
echo "Checking nginx config file..."
/etc/init.d/nginx configtest
echo "Starting nginx..."
nginx -g 'daemon off;'
echo "Nginx status is:"
/etc/init.d/nginx status
