echo "Update system"
apt update
apt upgrade -y

echo "Install apt packages"
apt install --no-install-recommends -y postgresql-server-dev-11 python3-dev gcc python3-pip postgresql

echo "Remove stale packages"
apt autoremove -y
