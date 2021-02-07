#!/bin/bash
# bi == Broker Interface
# Script should be at /usr/sbin, like /usr/sbin/set_pass_bi.sh and added to sudouers.
# Example of usage: set_pass_bi.sh -u tmp_user -p new_pass

read_arguments(){
  # read user passed arguments
  USAGE="$(basename "$0") -u user1, --username user1  -p new_pass, --password new_pass [-h, --help]"

  UNKNOWN=()
  USERNAME=""
  PASSWORD=""

  while [[ $# -gt 0 ]]
  do
    KEY="$1"
    case ${KEY} in
        -u|--username)
        USERNAME="$2"
        shift # past argument
        shift # past value
        ;;
        -p|--password)
        PASSWORD="$2"
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
    echo "Username can't be empty." >&2
    exit 1
  fi

  if [ -z "${PASSWORD}" ]; then
    echo "Password can't be empty." >&2
    exit 1
  fi

}

build_command(){
  SUDO_PATH="/usr/bin/sudo"
  COMMAND="/usr/sbin/chpasswd"
  FULL_COMMAND="echo ${USERNAME}:${PASSWORD} | ${SUDO_PATH} ${COMMAND}"
}

execute_command(){
  eval "${FULL_COMMAND}"
  exit 0
}

read_arguments "$@"

build_command

execute_command
