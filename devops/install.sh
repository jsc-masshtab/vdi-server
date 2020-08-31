#!/bin/bash

echo "Welcome to VDI server installer!"

echo "Select archiving type:"
echo "
    1. Periodic
    2. By count
"
echo "Type is:"
read TYPE

case $TYPE in
    1)
        echo "BY_COUNT=False" >> /tmp/vdi-install-vars

        echo "Select period:"
        echo "
        0. Every day
        1. Every week
        2. Every month
        3. Every year
        "
        echo "Period is:"
        read PERIOD

        case $PERIOD in
            0) echo "PARTITION=0" >> /tmp/vdi-install-vars ;;
            1) echo "PARTITION=1" >> /tmp/vdi-install-vars ;;
            2) echo "PARTITION=2" >> /tmp/vdi-install-vars ;;
            3) echo "PARTITION=3" >> /tmp/vdi-install-vars ;;
            *) echo "Error: Empty period!" && exit 1 ;;
        esac
        ;;
    2)
        echo "BY_COUNT=True" >> /tmp/vdi-install-vars

        echo "Count is (>0):"
        read COUNT

        echo "COUNT=$COUNT" >> /tmp/vdi-install-vars
        ;;
    *)
        echo "Error: Empty type!" && exit 1 ;;
esac

echo "Select path (for example: /tmp/):"
read PATH1
mkdir -p $PATH1
echo "PATH1=$PATH1" >> /tmp/vdi-install-vars

echo "CREATE=$(date +"%Y-%m-%d")" >> /tmp/vdi-install-vars

apt-get install ./vdi-*.deb -y