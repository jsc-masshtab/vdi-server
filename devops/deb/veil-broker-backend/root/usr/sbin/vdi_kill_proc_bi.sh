#!/bin/bash
# bi == Broker Interface
# Script should be at /usr/sbin, like /usr/sbin/kill_proc_bi.sh and added to sudoers.
# Example of usage: kill_proc_bi.sh -p 123

read_arguments(){
  # read user passed arguments
  USAGE="$(basename "$0") -p 123, --pid 123 [-h, --help]"

  UNKNOWN=()
  PROC_PID=""

  while [[ $# -gt 0 ]]
  do
    KEY="$1"
    case ${KEY} in
        -p|--pid)
        PROC_PID="$2"
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

  if [ -z "${PROC_PID}" ]; then
    echo "${USAGE}"
    print_arguments
    echo "Proc PID can't be empty."  >&2
    exit 1
  fi

}

print_arguments(){
  echo "Proc PID argument is: <<${PROC_PID}>>"
}

build_command(){
  SUDO_PATH="/usr/bin/sudo"
  COMMAND="/usr/bin/kill"

  FULL_COMMAND="${SUDO_PATH} ${COMMAND} ${PROC_PID}"
  echo "Full command: <<${FULL_COMMAND}>>"

}

execute_command(){
  ${FULL_COMMAND}
  exit 0
}

read_arguments "$@"

build_command

execute_command
