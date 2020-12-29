#!/bin/bash
readonly DB="$1"
readonly BACKUP="$2"
readonly PG_PORT="$3"
readonly IN_PORT="$4"

if [ -z "$5" ]; then
        iptables -t nat --flush repmgr_dnat
        iptables -t nat --flush repmgr_snat
        iptables -t nat -A repmgr_snat -p tcp -d $DB --dport $PG_PORT -j SNAT --to-source $BACKUP
fi
iptables -t nat -A repmgr_dnat -p tcp -d $BACKUP --dport $IN_PORT -j DNAT --to-destination $DB:$PG_PORT
