### Актуальная версия документации по проекту
    http://192.168.7.175/pages/viewpage.action?pageId=40993535
    http://confluence0.bazalt.team/pages/viewpage.action?pageId=40993535
    
### Запуск docker-контейнеров с БД и фронтом для локальной разработки:
    
    cd devops/docker && docker-compose up

### Шаблон для названий веток

    **feature**/**fix** **tg** {task#/us#}  -- feature tg 5467
    
### Шаблон для коммита в Git

    FEATURE TG-6022 Sanic -> Tornado migration -- HEAD
    
    Websockets configuration + base pool examples -- BODY

**Veil VDI project structure**

    backend/: A directory with backend files (Tornado and etc.)
        auth/ -- direcory with auth modules
            utils/ -- directory with auth utils
               __init__.py
                crypto -- Utils for cryptographic encode/decode passwords for Controllers.
                django_crypto.py -- Django's standard crypto functions and utilities.
                hashers.py -- Django's standard hashers.
                veil_jwt -- JWT utils for Tornado                        
            __init__.py
            schema.py -- GraphQL schema
            models.py -- Sqlalchemy models description.
            urls.py -- Tornado urls
            handlers.py -- Tornado handlers
        common/ -- Common used utilites, like Django's standard functions and utilities.
            __init__.py
            veil_errors.py -- Common errors with handlers.
            veil_validators -- Commin validators for GraphQL schema
            veil_handlers.py -- Base handlers for Tornado 
            veil_decorators -- Common used decorators.
            veil_client -- Base ECP-client module.
            utils -- Old utility functions from VDI v.0.2
        thin_client_api/
            __init__.py
            handlers.py -- Tornado handlers used by thin_client (desktop-client-c).
            urls.py -- Routes for thin_client.
        migrations/ -- Database migrations.
            versions/ -- migrations directory. 
        tests/  -- All project tests
            snapshots/ -- snapshots (test results) for some of test cases.
            fixtures --PyTest fixtures
            pytest.ini
            utils -- Some extra utils for Async testing with GraphQL and PyTest. 
        app.py -- main module for starting service.
        database.py -- Abstract classes for GINO and Sqlalchemy
        manage.py -- deployment script
        settings.py -- Project settings
        alembic.ini -- alembic configuration.
        __init__.py
    desktop-client/ -- old thin client - Python realization.
    desktop-client-c/ -- new thin client - C++ realization.
    frontend/ -- all frontend files
    devops/: -- devops files.
        conf/ -- configuration files for other services (like supervisor, logrotate and etc.)
            nginx.conf -- nginx configuration file
            supervisord.conf -- supervisor basic fonfiguration
            veil-vdi -- logrotate configuration
            veil-vdi-angular.supervisor -- supervisor configuration for starting angular
            veil-vdi-tornado -- supervisor configuration for vdi-backend service
        manage.sh -- project control script
    .gitignore

    #test
