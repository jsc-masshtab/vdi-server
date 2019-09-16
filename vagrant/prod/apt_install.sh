echo "Install apt packages"

#sed -i s/us\./ru\./g /etc/apt/sources.list
apt update -y
apt install --no-install-recommends -y postgresql-server-dev-9.6 python3-dev gcc python3-pip postgresql htop  mc 
# Не нашел на астре пакеты ncdu и bmon
