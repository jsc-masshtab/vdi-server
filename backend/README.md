### Alembic
```shell script
export PYTHONPATH=~/PycharmProjects/vdiserver/backend/main_app

alembic revision --autogenerate -m "Controller credentials"

alembic upgrade head

alembic revision -m "create account table"

alembic merge heads
```

### Tests

Для запуска тестов через PyCharm необходимо установить "**Default test runner**" - "**pytest**"

Чтобы обновить результаты выполнения snapshot - `pytest --snapshot-update`


Для запуска тестов из консоли перейти в каталог backend и запустить 'pytest main_app/tests'. Если нужно запустить
специфичные тесты, указать **-m**, например `pytest main_app/tests -m "auth"` - этот набор запустит все тесты 
Пользователей, AD и аутентификации.
