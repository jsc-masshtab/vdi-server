#!/bin/bash

# Скрипт синхронизации репозиториев vdi с публичными репозиториями на хостинге github.

# Перед запуском скрипта необходимо внести учетные данные от действующего пользователя местного gitlab.

# Пользователь и пароль от github в БД KeepassX. Пароль от БД KeepassX выдается ответственными людьми.
# На данный это Д.Проскурин и С.Алексанков.

# Для доступ к github используется токен - https://github.com/settings/tokens

#MASHTAB_USER="vdi_deploy"
#MASHTAB_TOKEN="..."

#GITHUB_USER="masshtab"
#GITHUB_TOKEN="..."

#veil-connect
cd /tmp
rm -rf veil-connect
git clone http://$MASHTAB_USER:$MASHTAB_TOKEN@gitlab.bazalt.team/vdi/veil-connect.git
cd veil-connect
git remote add github https://github.com/jsc-masshtab/veil-connect
git push -u https://$GITHUB_USER:$GITHUB_TOKEN@github.com/jsc-masshtab/veil-connect master --tags

#veil-api-client
cd /tmp
rm -rf veil-api-client
git clone http://$MASHTAB_USER:$MASHTAB_TOKEN@gitlab.bazalt.team/vdi/veil-api-client.git
cd veil-api-client
git remote add github https://github.com/jsc-masshtab/veil-api-client
git push -u https://$GITHUB_USER:$GITHUB_TOKEN@github.com/jsc-masshtab/veil-api-client master --tags

#veil-aio-au
cd /tmp
rm -rf veil-aio-au
git clone http://$MASHTAB_USER:$MASHTAB_TOKEN@gitlab.bazalt.team/vdi/veil-aio-au.git
cd veil-aio-au
git remote add github https://github.com/jsc-masshtab/veil-aio-au
git push -u https://$GITHUB_USER:$GITHUB_TOKEN@github.com/jsc-masshtab/veil-aio-au master --tags

#vdi-server
cd /tmp
rm -rf vdi-server
git clone http://$MASHTAB_USER:$MASHTAB_TOKEN@gitlab.bazalt.team/vdi/vdi-server.git
cd vdi-server
git remote add github https://github.com/jsc-masshtab/vdi-server
git push -u https://$GITHUB_USER:$GITHUB_TOKEN@github.com/jsc-masshtab/vdi-server dev --tags