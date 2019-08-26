echo "Install apt packages"

sed -i s/us\./ru\./g /etc/apt/sources.list

apt install --no-install-recommends -y postgresql-server-dev-11 python3-dev gcc python3-pip postgresql
