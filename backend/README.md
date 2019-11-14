1. Шаблон для названий веток:

    **feature**/**fix** **tg** {task#/us#}  -- feature tg 5467
    
2. Шаблон для коммита в Git:

    FEATURE TG-6022 Sanic -> Tornado migration -- HEAD
    
    Websockets configuration + base pool examples -- BODY
    
3. Alembic

export PYTHONPATH=~/PycharmProjects/vdiserver/backend/vdi2/

alembic revision --autogenerate -m "Controller credentials"

alembic upgrade head

alembic revision -m "create account table"