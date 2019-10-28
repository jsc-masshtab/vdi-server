    code/: A directory with all Developers files
        veil-vdi/: directory with all developers files for veil-vdi project
            backend/
                auth/ -- direcory with auth modules
                    utils/ -- directory with auth utils
                        __init__.py
                        crypto.py -- Django's standard crypto functions and utilities. Возможно переедет в auth
                        hashers.py -- Django's standard hashers. Возможно переедет в auth
                        veil_jwt -- JWT utils for Tornado                        
                    __init__.py
                    handlers.py -- auth handlers (not graphana)
                    urls.py -- auth urls
                    schema.py -- Graphana hanglers
                    models.py -- sqlalchemy models description
                controller/
                common/ -- Common used utilites, like Django's standard functions and utilities.
                    __init__.py
                    veil_errors.py -- Old errors moved from Vdi v0
                    veil_handlers.py -- Base handlers for Tornado 
                app.py -- ?
                database.py -- ?
                manage.py -- ?
                settings.py -- Project settings
                local_settings.py.template -- Project local settings
                alembic.ini -- ?
                __init__.py
               pool/ -- directory with pool modules
                    __init__.py
                    handlers.py
                    models.py
                    schema.py
                    urls.py
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
