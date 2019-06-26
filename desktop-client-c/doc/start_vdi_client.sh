#!/bin/bash


ABSOLUTE_FILENAME=`readlink -e "$0"`

DIRECTORY=`dirname "$ABSOLUTE_FILENAME"`

#killall virt_viewer_veil


#CURDATE=`date +%Y.%m.%d`
#CURDATETIME=`date +%Y.%m.%d_%H.%M.%S`


#LOGDIRWITHDATE="/logs/${CURDATE}/${CURDATETIME}"
#LOGDIR="$DIRECTORY/logs"

#mkdir -p "$LOGDIRWITHDATE"
#rm -rf "$LOGDIR"
#ln -s "$LOGDIRWITHDATE" "$LOGDIR"


export LD_LIBRARY_PATH=$DIRECTORY/libs

./virt_viewer_veil
