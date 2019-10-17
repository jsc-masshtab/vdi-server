    code/: A directory with all Developers files
        veil-vdi/: directory with all developers files for veil-vdi project
            backend/
                auth/ -- direcory with auth modules 
                    __init__.py
                    handlers.py -- package handlers (not graphana)
                    urls.py -- package urls
                    schema.py -- pachage graphana danglers
                    models.py -- sqlalchemy models description
                controller/
                common/ -- Common used utilites, like Django's standard functions and utilities.
                    __init__.py
                    crypto.py -- Django's standard crypto functions and utilities. Возможно переедет в auth
                    hashers.py -- Django's standard hashers. Возможно переедет в auth
                    errors.py -- Old errors moved from Vdi v0 
                app.py -- ?
                database.py -- ?
                manage.py -- ?
                settings.py -- Project settings
                local_settings.py.template -- Project local settings
                alembic.ini -- ?
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
