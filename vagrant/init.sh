echo "Upgrade arch..."
pacman --noconfirm -Syu

echo "Installing packages..."
pacman --noconfirm -S --needed base-devel
pacman --noconfirm -S python-pip postgresql git nodejs npm

python -m pip install pipenv

echo "Init database"
systemctl stop postgresql
echo "Setting postgresql..."
su postgres -c "initdb -D /var/lib/postgres/data"
systemctl enable postgresql
systemctl start postgresql

sudo su postgres -c "psql -c \"drop database vdi;\" "
sudo su postgres -c "psql -c \"create database vdi;\" "


# Remove *.pyc files
find /vagrant -name "*.pyc" -delete