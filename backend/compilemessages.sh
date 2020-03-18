#!/bin/bash 
# get arguments and init variables
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <locales> [optional: <domain_name>]"
    exit 1
fi
locales=$1
domain="messages"
if [ ! -z "$2" ]; then
    domain=$2
fi
locales_dir="locales/${locales}/LC_MESSAGES"
po_file="${locales_dir}/${domain}.po"
mo_file="${locales_dir}/${domain}.mo"
# create .mo file from .po
msgfmt ${po_file} --output-file=${mo_file}