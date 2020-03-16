#!/bin/bash

APP_DIR=/opt/veil-vdi
cd $APP_DIR

rm -rf $APP_DIR/backend
cp -r /vagrant/backend $APP_DIR/backend

rm -rf $APP_DIR/devops
cp -r /vagrant/devops $APP_DIR/devops