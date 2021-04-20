#!/bin/bash

read_arguments(){
  # read user passed arguments
  USAGE="$(basename "$0") -v 2, --version 3 [-h, --help]"

  UNKNOWN=()
  VERSION=""

  while [[ $# -gt 0 ]]
  do
    KEY="$1"
    case ${KEY} in
        -v|--version)
        VERSION="$2"
        shift # past argument
        shift # past value
        ;;
        -h|--help)
        echo "${USAGE}"
        exit 0
        ;;
        *)    # unknown option
          UNKNOWN+=("$1") # save it in an array for later
        shift # past argument
        ;;
    esac
  done

  if [ -n "${UNKNOWN}" ]; then
    echo "${USAGE}"
    print_arguments
    echo "Unknown arguments: ${UNKNOWN}" >&2
    exit 1
  fi

  if [ -z "${VERSION}" ]; then
    echo "${USAGE}"
    print_arguments
    echo "Version can't be empty." >&2
    exit 1
  fi

  if [ "${VERSION}" == "2" ]; then
    echo "Миграция с версии 2!"
  elif [ "${VERSION}" == "3" ]; then
    echo "Миграция с версии 3!"
  else
    print_arguments
    echo "Possible versions are: 2 or 3." >&2
    exit 1
  fi

}

print_arguments(){

  echo "version argument is: <<${VERSION}>>"

}

welcome_text(){

  echo "Добро пожаловать в утилиту миграции VeiL Broker."
  echo "Пожалуйста, удостоверьтесь, в том, что"
  echo "при миграции с версии 2 установлена версия 2.1.4 "
  echo "или при миграции на версию 3 установлена версия 3.0.0"

}

update_python_req(){
  /opt/veil-vdi/env/bin/python3 -m pip install 'veil-api-client==2.2.1' --force-reinstall
}

postgres_make_dumps(){
  sudo -u postgres pg_dump vdi --column-inserts --no-owner -a -t user_for_export -t group -t mapping -t entity > /tmp/broker_pt_1.sql
  sudo -u postgres pg_dump vdi --column-inserts --no-owner -a -t controller -t authentication_directory -t group_role -t pool_for_export -t entity_owner > /tmp/broker_pt_2.sql
  sudo -u postgres pg_dump vdi --column-inserts --no-owner -a -t user_groups -t user_role -t automated_pool -t group_authentication_directory_mappings -t static_pool -t vm > /tmp/broker_pt_3.sql
}

migrate_from_2(){
  echo "Останавливаем сервисы..."
  sudo /etc/init.d/nginx stop
  sudo supervisorctl stop vdi-pool_worker
  sudo supervisorctl stop vdi-server-8888
  sudo supervisorctl stop vdi-ws_listener_worker

  echo "Начинаем процесс переноса данных из версии 2..."
  update_python_req
  export PYTHONPATH=/opt/veil-vdi/app && cd /opt/veil-vdi/app && /opt/veil-vdi/env/bin/python broker_v2.py
  postgres_make_dumps

  echo "Процесс подготовки данных завершен. Выполните перенос получившихся файлов на версию 3."
  echo "/tmp/broker_pt_1.sql"
  echo "/tmp/broker_pt_2.sql"
  echo "/tmp/broker_pt_3.sql"
}

migrate_from_3(){
  echo "Останавливаем сервисы..."
  sudo /etc/init.d/apache2 stop
  sudo service vdi-pool_worker stop
  sudo service vdi-web stop
  sudo service vdi-ws_listener stop

  echo "Начинаем процесс переноса данных из версии 2 на версию 3..."
  echo "Убедитесь, что файлы broker_pt_1.sql, broker_pt_2.sql, broker_pt_3.sql находятся в каталоге /tmp"
  echo "На момент миграции в версии 3.0.0 не должно быть иных пользователей, кроме, vdiadmin."
  export PYTHONPATH=/opt/veil-vdi/app && cd /opt/veil-vdi/app && sudo -u vdiadmin /opt/veil-vdi/env/bin/python broker_v3.py

  echo "Задайте вновь созданным заблокированным пользователем пароли."
  echo "Процесс подготовки данных завершен."
  sudo service vdi-pool_worker start
  sudo service vdi-web start
  sudo service vdi-ws_listener start
  sudo /etc/init.d/apache2 start

}

run_migration(){
  if [ "${VERSION}" == "2" ]; then
    migrate_from_2
  fi
  if [ "${VERSION}" == "3" ]; then
    migrate_from_3
  fi
  exit 0
}

# Execution starts here
read_arguments "$@"
welcome_text
print_arguments
run_migration
