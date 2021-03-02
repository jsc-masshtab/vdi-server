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
  var1=$(grep -c "msgstr \"\"" "${po_file}")
  var2=$(grep -c "fuzzy" "${po_file}")
  var3=$(grep -c "\.\"\|\:\"" "${po_file}")
  var4=$(grep -c -E "msgstr|msgid" "${po_file}")

  if [ "${var1}" -gt 1 ] || [ "${var2}" -gt 0 ] || [ "$((${var4} - ${var3}))" -gt 2 ]; then
    echo "Rows ending without :/. is $((${var4} - ${var3} - 2))"
    echo "Locale: ${locale}"
    echo "Var 1: ${var1}"
    echo "Var 2: ${var2}"
    echo "Var 3: ${var3}"
    echo "Var 4: ${var4}"
    echo "Error code 1"
    exit 1
  fi

  # create .mo file from .po
  msgfmt "${po_file}" --output-file="${mo_file}"
  echo "Translation created or updated for $locale locale"
done
