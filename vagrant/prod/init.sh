
sed -i 's/peer/trust/g' /etc/postgresql/9.6/main/pg_hba.conf
systemctl restart postgresql

echo 'postgres:postgres' | chpasswd
su postgres -c "psql -c \"ALTER ROLE postgres PASSWORD 'postgres';\" "
su postgres -c "psql -c \"create database vdi encoding 'utf8' lc_collate = 'C.UTF-8' lc_ctype = 'C.UTF-8' template template0;\" "

python3.5 -m pip install pipenv

