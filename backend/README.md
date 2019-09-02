
1. [Скачиваем](https://docs.conda.io/en/latest/miniconda.html) миниконду. Пусть мы установили её в `conda_dir`.
2. В директории `backend` (то есть, именно там, где лежит environment.yml) запускаем

```
conda_dir/bin/conda env update
```

3. Запускаем сервис:

```
conda_dir/bin/vdi
```

4. Можем сделать из `conda_dir` архив и сказать, что это релиз.