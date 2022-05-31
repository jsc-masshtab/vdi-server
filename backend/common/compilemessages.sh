#!/bin/bash 
# get arguments and init variables
#if [ "$#" -lt 1 ]; then
#    echo "Usage: $0 <locales> [optional: <domain_name>]"
#    exit 1
#fi

for locale in en ru
do
  locales="$locale"
  domain="messages"
  if [ -n "$2" ]; then
      domain=$2
  fi
  locales_dir="./locales/${locales}/LC_MESSAGES"
  po_file="${locales_dir}/${domain}.po"
  mo_file="${locales_dir}/${domain}.mo"
  fuzzy_count=$(grep -c "fuzzy" "${po_file}")

  if [ "${fuzzy_count}" -gt 0 ]; then
    echo "Locale: ${locale}"
    echo "Fuzzy translation detected. Fix translation and remove fuzzy keywords: ${fuzzy_count}"
    echo "Error code 1"
    exit 1
  fi

  # create .mo file from .po
  msgfmt "${po_file}" --output-file="${mo_file}"
  echo "Translation created or updated for $locale locale"
done
