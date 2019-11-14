    code/: A directory with all Developers files
        veil-vdi/: directory with all developers files for veil-vdi project
            backend/
                auth/ -- direcory with auth modules
                    utils/ -- directory with auth utils
                        __init__.py
                        crypto -- Utils for cryptographic encode/decode passwords for Controllers.
                        django_crypto.py -- Django's standard crypto functions and utilities.
                        hashers.py -- Django's standard hashers.
                        veil_jwt -- JWT utils for Tornado                        
                    __init__.py
                    schema.py -- Graphana hanglers. WIP.
                    models.py -- Sqlalchemy models description.
                controller/
                common/ -- Common used utilites, like Django's standard functions and utilities.
                    __init__.py
                    veil_errors.py -- Common errors with handlers. WIP Logging.
                    veil_handlers.py -- Base handlers for Tornado 
                    veil_decorators -- Common used decorators.
                    utils -- Old utility functions from VDI v.0
                thin_client_api/
                    __init__.py
                    handlers.py -- Tornado handlers used by thin_client (desktop-client-c).
                    urls.py -- Routes for thin_client.
                migrations/
                    versions/ -- Database migrations. 
                app.py -- main module for starting service.
                database.py -- ?
                manage.py -- ?
                settings.py -- Project settings
                alembic.ini -- alembic configuration.
                __init__.py
            desktop-client/
            desktop-client-c/
            frontend/
    devops/:
        conf/
            nginx.conf -- 
            supervisord.conf
        docs/: directory containing project documentation
            README.md
            LICENSE
            TODO: move project structure here
    .gitignore
