
1. [Скачиваем](https://docs.conda.io/en/latest/miniconda.html) миниконду. Пусть мы установили её в `conda_dir`.
2. В директории `backend` (то есть, именно там, где лежит environment.yml) запускаем

```
conda_dir/bin/conda env update
```

3. Инициализируем базу

```
mkdir ~/pgdata
conda_dir/bin/initdb --data ~/pgdata
conda_dir/bin/pg_ctl -D ~/pgdata -l logfile start
conda_dir/bin/createuser --superuser postgres
conda_dir/bin/psql -c "create database vdi encoding 'utf8' lc_collate = 'en_US.UTF-8' lc_ctype = 'en_US.UTF-8' template template0;" -U postgres
```

Запускаем миграции

```
conda_dir/bin/mi apply
```

4. Запускаем сервис:

```
conda_dir/bin/vdi
```
