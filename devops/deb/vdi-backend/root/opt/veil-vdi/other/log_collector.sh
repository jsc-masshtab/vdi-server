#!/bin/bash

VDI_LOG_PATH="/var/log/veil-vdi"
APACHE_LOG_PATH="/var/log/apache2"
NGINX_LOG_PATH="/var/log/nginx"
POSTGRESQL_LOG_PATH="/var/log/postgresql"
REDIS_LOG_PATH="/var/log/redis"
DATE=$(date +"%Y%m%d%H%M%S")

echo "Select archiving type:"
echo "
    1. Last (only *.log files)
    2. Full (all logs, include *.gz files)
"
echo "Type is:"
read TYPE

case $TYPE in
    1)
        tar -czf /tmp/vdi_server_logs_$DATE.tar.gz $VDI_LOG_PATH/*.log $APACHE_LOG_PATH/*.log $NGINX_LOG_PATH/*.err $NGINX_LOG_PATH/*.acc $POSTGRESQL_LOG_PATH/*.log $REDIS_LOG_PATH/*.log ;;
    2)
        tar -czf /tmp/vdi_server_logs_$DATE.tar.gz $VDI_LOG_PATH $APACHE_LOG_PATH $NGINX_LOG_PATH $POSTGRESQL_LOG_PATH $REDIS_LOG_PATH ;;
    *)
        echo "Error: Empty type!" && exit 1 ;;
esac

echo "VeiL Broker logs saved in /tmp/vdi_server_logs_$DATE.tar.gz"