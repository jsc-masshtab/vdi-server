### VeiL VDI
VeiL VDI allows to create user desktops in virtual machines hosted on 
dedicated servers.
Connection broker VeiL VDI should be installed on the trusted OS Astra linux 1.6 SE (for version 3.0 and higher) 
or OS Astra linux 1.7 SE (for version 4.0 and higher).

### Alembic
```shell script
cd ~/vdi-server/backend/common/migrations

export PYTHONPATH=~/vdi-server/backend

alembic revision --autogenerate -m "Controller credentials"

alembic upgrade head

alembic revision -m "create account table"

alembic merge heads
```

### Docs
    https://veil.mashtab.org/vdi-docs/
    
### Running docker with a db and frontend for local development:
    cd devops/docker && docker-compose up
