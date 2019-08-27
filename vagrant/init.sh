
sed -i 's/peer/trust/g' /etc/postgresql/11/main/pg_hba.conf
systemctl restart postgresql

echo 'postgres:postgres' | chpasswd
su postgres -c "psql -c \"ALTER ROLE postgres PASSWORD 'postgres';\" "
su postgres -c "psql -c \"drop database vdi;\" "
su postgres -c "psql -c \"create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8';\" "

python3 -m pip install pipenv

