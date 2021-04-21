# Руководство для установки на linux

1. установить в любой python интерпретатор пакет mkdocs [mkdocs](https://www.mkdocs.org)
`{python_env}/bin/pip install mkdocs`

1. Поставить темы для mkdocs
    1. [mkdocs-material](https://squidfunk.github.io/mkdocs-material/).
    `{python_env}/bin/pip install mkdocs-material`
    
    1. [pymdown-extensions](https://squidfunk.github.io/mkdocs-material/extensions/pymdown/).
    `{python_env}/bin/pip install pymdown-extensions`

    1. [mkdocs-print-site-plugin](https://github.com/timvink/mkdocs-print-site-plugin).
    `{python_env}/bin/pip install mkdocs-print-site-plugin`
       
1. При необходимости поставить экспорт в pdf для mkdocs ПРИ СБОРКЕ
    1. [mkdocs-pdf-export-plugin](https://github.com/zhaoterryy/mkdocs-pdf-export-plugin/).
    `{python_env}/bin/pip install mkdocs-pdf-export-plugin`
    
1. перейти в каталог vdi-server **docs**

1. Запустить `{python_env}/bin/mkdocs build -f toc.yaml -d ./docs`

1. Запуск в VeiL Broker

    1. скопировать появившийся каталог **docs** в **/opt/veil-vdi**
    
    2. Проверить документацию на [docs](http://{broker_ip}/docs).
    
1. Запуск локально

    6.1. Запустить `{python_env}/bin/mkdocs serve -f toc.yaml`

    6.2. Проверить документацию на [docs](http://127.0.0.1:8000).
 
