cd /vagrant/backend

wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p conda_dir

conda_dir/bin/conda env update

mkdir ~/pgdata
conda_dir/bin/initdb --data ~/pgdata
conda_dir/bin/pg_ctl -D ~/pgdata -l logfile start
conda_dir/bin/createuser --superuser postgres
conda_dir/bin/psql -c "create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;" -U postgres

conda_dir/bin/mi apply