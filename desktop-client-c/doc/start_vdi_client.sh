#!/bin/bash


ABSOLUTE_FILENAME=`readlink -e "$0"`

DIRECTORY=`dirname "$ABSOLUTE_FILENAME"`

#killall thin_client_veil


#CURDATE=`date +%Y.%m.%d`
#CURDATETIME=`date +%Y.%m.%d_%H.%M.%S`
#LOGDIRWITHDATE="/logs/${CURDATE}/${CURDATETIME}"
#LOGDIR="$DIRECTORY/logs"

mkdir -p "$DIRECTORY/log"


export LD_LIBRARY_PATH=$DIRECTORY/libs
export GDK_PIXBUF_MODULEDIR=$DIRECTORY/pixbuf_loaders

cd $DIRECTORY
./thin_client_veil $1
