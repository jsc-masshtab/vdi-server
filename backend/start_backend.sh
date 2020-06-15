#!/bin/bash 

python ws_listener_worker/ws_listener_worker.py &
#python pool_worker/pool_worker.py &
python main_app/app.py &









