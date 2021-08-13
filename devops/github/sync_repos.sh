#!/bin/bash

# Скрипт синхронизации репозиториев vdi с публичными репозиториями на хостинге github.

# Перед запуском скрипта необходимо внести учетные данные от действующего пользователя местного gitlab.

# Пользователь и пароль от github в БД KeepassX. Пароль от БД KeepassX выдается ответственными людьми.
# На данный это Д.Проскурин и С.Алексанков.

# Для доступ к github используется токен - https://github.com/settings/tokens

MASHTAB_USER="d.proskurin"
MASHTAB_PASS="..."

GITHUB_USER="masshtab"
GITHUB_PASS="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"

#veil-connect
cd /tmp
rm -rf veil-connect
git clone http://$MASHTAB_USER:$MASHTAB_PASS@gitlab.bazalt.team/vdi/veil-connect.git
cd veil-connect
git remote add github https://github.com/jsc-masshtab/veil-connect
git push -u https://$GITHUB_USER:$GITHUB_PASS@github.com/jsc-masshtab/veil-connect master --tags

#veil-api-client
cd /tmp
rm -rf veil-api-client
git clone http://$MASHTAB_USER:$MASHTAB_PASS@gitlab.bazalt.team/vdi/veil-api-client.git
cd veil-api-client
git remote add github https://github.com/jsc-masshtab/veil-api-client
git push -u https://$GITHUB_USER:$GITHUB_PASS@github.com/jsc-masshtab/veil-api-client master --tags

#veil-aio-au
cd /tmp
rm -rf veil-aio-au
git clone http://$MASHTAB_USER:$MASHTAB_PASS@gitlab.bazalt.team/vdi/veil-aio-au.git
cd veil-aio-au
git remote add github https://github.com/jsc-masshtab/veil-aio-au
git push -u https://$GITHUB_USER:$GITHUB_PASS@github.com/jsc-masshtab/veil-aio-au master --tags
