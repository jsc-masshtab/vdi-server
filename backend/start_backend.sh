#!/bin/bash 

ABSOLUTE_FILENAME=`readlink -e "$0"`
DIRECTORY=`dirname "$ABSOLUTE_FILENAME"`

export PYTHONPATH=$DIRECTORY/main_app/

python ws_listener_worker/ws_listener_worker.py &
python pool_worker/pool_worker.py &
python main_app/app.py &









