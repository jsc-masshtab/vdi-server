#!/bin/bash 

ABSOLUTE_FILENAME=`readlink -e "$0"`
DIRECTORY=`dirname "$ABSOLUTE_FILENAME"`

export PYTHONPATH=$DIRECTORY/main_app/ # todo: temp

# Stop backend processes
sh stop_backend.sh > /dev/null 2>&1

# Start processes
python ws_listener_worker/ws_listener_worker.py &
python pool_worker/pool_worker.py & 
python main_app/app.py --access_to_stdout=True --logging=debug --port=8888 --debug=True --autoreload=False --workers=1 &  # --log_file_prefix=/var/log/veil-vdi/vdi_tornado.log










