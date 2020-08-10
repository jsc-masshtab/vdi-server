#!/bin/bash

DIR=`python ../../settings.py`

if search=$(sudo find $DIR -name "event_*.csv" -exec echo -n "1" \;); [ "$search" = "" ]
then
echo "Have not journal files"
else
echo "Archived journal files from $DIR to ${DIR}archives"
nm=$(sudo find $DIR -name "event_*.csv")
sudo mkdir -p $DIR/archives
sudo chmod 777 archives/
sudo zip -m ./archives/${nm}.zip -9 $DIR/*.csv
fi