### Шаблон для названий веток

    **feature**/**fix** **tg** {task#/us#}  -- feature tg 5467
    
### Шаблон для коммита в Git

    FEATURE TG-6022 Sanic -> Tornado migration -- HEAD
    
    Websockets configuration + base pool examples -- BODY
    
### Alembic
```shell script
export PYTHONPATH=~/PycharmProjects/vdiserver/backend

alembic revision --autogenerate -m "Controller credentials"

alembic upgrade head

alembic revision -m "create account table"

alembic merge heads
```

### Tests

Для запуска тестов через PyCharm необходимо установить "**Default test runner**" - "**pytest**"

Чтобы обновить результаты выполнения snapshot - `pytest --snapshot-update`

Для запуска тестов из консоли перейти в каталог tests и запустить `pytest`, если нужно запустить
специфичные тесты, указать **-m**, например `pytest -m "auth"` - этот набор запустит все тесты 
Пользователей, AD и аутентификации.