#!/bin/bash
# bi == Broker Interface
# Script should be at /usr/sbin, like /usr/sbin/edituser_bi.sh and added to sudouers.
# Example of usage: edituser_bi.sh -u tmp_user -L

read_arguments(){
  # read user passed arguments
  USAGE="$(basename "$0") -u user1 [-с new GECOS value][-e expire date][-f inactive period][-a append user to a group][-L lock user][-U unlock user][-h, --help]"

  UNKNOWN=()
  USERNAME=""
  COMMENT=""
  EXPIRE_DATE=""
  INACTIVE_PERIOD=""
  GROUPNAME=""
  LOCK=NO
  UNLOCK=NO

  while [[ $# -gt 0 ]]
  do
    KEY="$1"
    case ${KEY} in
        -u)
        USERNAME="$2"
        shift # past argument
        shift # past value
        ;;
        -c)
        COMMENT="$2"
        shift # past argument
        shift # past value
        ;;
        -e)
        EXPIRE_DATE="$2"
        shift # past argument
        shift # past value
        ;;
        -f)
        INACTIVE_PERIOD="$2"
        shift # past argument
        shift # past value
        ;;
        -a)
        GROUPNAME="$2"
        shift # past argument
        shift # past value
        ;;
        -L)
        LOCK="$2"
        shift # past argument
        shift # past value
        LOCK=YES
        ;;
        -U)
        UNLOCK="$2"
        shift # past argument
        shift # past value
        UNLOCK=YES
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

}

print_arguments(){
  echo "user argument is: <<${USERNAME}>>"
  echo "group argument is: <<${GROUPNAME}>>"
  echo "comment argument is: <<${COMMENT}>>"
  echo "expire argument is: <<${EXPIRE_DATE}>>"
  echo "inactive argument is: <<${INACTIVE_PERIOD}>>"
  echo "lock argument is: <<${LOCK}>>"
  echo "unlock argument is: <<${UNLOCK}>>"
}

build_command(){

  SUDO_PATH="/usr/bin/sudo"
  COMMAND="/usr/sbin/usermod"

  if [ -n "${COMMENT}" ]; then
    COMMAND="${COMMAND} --comment ${COMMENT}"
  fi

  if [ -n "${EXPIRE_DATE}" ]; then
    COMMAND="${COMMAND} --expiredate ${EXPIRE_DATE}"
  fi

  if [ -n "${INACTIVE_PERIOD}" ]; then
    COMMAND="${COMMAND} --inactive ${INACTIVE_PERIOD}"
  fi

  if [ ${LOCK} == YES ]; then
    COMMAND="${COMMAND} --lock"
  fi

  if [ ${UNLOCK} == YES ]; then
    COMMAND="${COMMAND} --unlock"
  fi

  if [ -n "${GROUPNAME}" ]; then
    COMMAND="${COMMAND} --append --groups ${GROUPNAME}"
  fi

  FULL_COMMAND="${SUDO_PATH} ${COMMAND} ${USERNAME}"
  echo "Full command: <<${FULL_COMMAND}>>"

}

execute_command(){
  ${FULL_COMMAND}
  exit 0
}

read_arguments "$@"

build_command

execute_command
