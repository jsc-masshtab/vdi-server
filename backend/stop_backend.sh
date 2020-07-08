#!/bin/bash
# по-хорошему
killall -s SIGTERM python  > /dev/null 2>&1
killall -s SIGTERM python3  > /dev/null 2>&1
killall -s SIGTERM python3.5  > /dev/null 2>&1

sleep 1

# по-плохому
killall -9 python  > /dev/null 2>&1
killall -9 python3  > /dev/null 2>&1
killall -9 python3.5  > /dev/null 2>&1
