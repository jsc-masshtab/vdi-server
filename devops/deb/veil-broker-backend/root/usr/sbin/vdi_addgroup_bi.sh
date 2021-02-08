#!/bin/bash
# bi == Broker Interface
# Script should be at /usr/sbin, like /usr/sbin/adduser_bi.sh and added to sudouers.
# Example of usage: addgroup_bi.sh -g group1

read_arguments(){
  # read user passed arguments
  USAGE="$(basename "$0") -g group1, --groupname group1 [-h, --help]"

  UNKNOWN=()
  GROUPNAME=""

  while [[ $# -gt 0 ]]
  do
    KEY="$1"
    case ${KEY} in
        -g|--groupname)
        GROUPNAME="$2"
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

  if [ -z "${GROUPNAME}" ]; then
    echo "${USAGE}"
    print_arguments
    echo "Groupname can't be empty."  >&2
    exit 1
  fi

}

print_arguments(){
  echo "group argument is: <<${GROUPNAME}>>"
}

build_command(){
  SUDO_PATH="/usr/bin/sudo"
  COMMAND="/usr/sbin/addgroup"

  FULL_COMMAND="${SUDO_PATH} ${COMMAND} ${GROUPNAME}"
  echo "Full command: <<${FULL_COMMAND}>>"

}

execute_command(){
  ${FULL_COMMAND}
  exit 0
}

read_arguments "$@"

build_command

execute_command
