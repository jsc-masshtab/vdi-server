echo "Adding no password check for existing records in pg_hba.conf"
sed -i 's/peer/trust/g' /var/lib/postgresql/data/pg_hba.conf
sed -i 's/md5/trust/g' /var/lib/postgresql/data/pg_hba.conf

echo "Extending max connections in postgresql.conf"
sed -i 's/max_connections = 100	/max_connections = 1000	/g' /var/lib/postgresql/data/postgresql.conf

echo "Creatind database vdi"
psql -c "create database vdi encoding 'utf8' lc_collate = 'C.UTF-8' lc_ctype = 'C.UTF-8' template template0;" -U postgres
