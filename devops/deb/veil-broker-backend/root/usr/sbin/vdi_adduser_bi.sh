#!/bin/bash
# bi == Broker Interface
# Script should be at /usr/sbin, like /usr/sbin/adduser_bi.sh and added to sudouers.
# Example of usage: adduser_bi.sh -u tmp_user -G 'Full user name,,,Vdi-broker' -g vdi-broker-users

read_arguments(){
  # read user passed arguments
  USAGE="$(basename "$0") -u user1, --username user1  [-g existing_group, --group existing_group] [-G GECOS_STR, --gecos GECOS_STR] [-h, --help]"

  UNKNOWN=()
  USERNAME=""
  GECOS=""

  while [[ $# -gt 0 ]]
  do
    KEY="$1"
    case ${KEY} in
        -u|--username)
        USERNAME="$2"
        shift # past argument
        shift # past value
        ;;
        -g|--group)
        GROUP="$2"
        shift # past argument
        shift # past value
        ;;
        -G|--GECOS)
        GECOS="$2"
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

  if [ -z "${USERNAME}" ]; then
    echo "${USAGE}"
    print_arguments
    echo "Username can't be empty." >&2
    exit 1
  fi

}

print_arguments(){
  echo "user argument is: <<${USERNAME}>>"
  echo "group argument is: <<${GROUP}>>"
  echo "gecos argument is: <<${GECOS}>>"
}

build_command(){
  SUDO_PATH="/usr/bin/sudo"
  COMMAND="/usr/sbin/adduser --disabled-login --no-create-home --shell /sbin/nologin --quiet"

  if [ -n "${GROUP}" ]; then
    COMMAND="${COMMAND} --ingroup ${GROUP}"
  fi

  FULL_COMMAND="${SUDO_PATH} ${COMMAND} --gecos '${GECOS}' ${USERNAME}"
  echo "Full command: <<${FULL_COMMAND}>>"

}

execute_command(){
  eval "${FULL_COMMAND}"
  exit 0
}

read_arguments "$@"

build_command

execute_command
