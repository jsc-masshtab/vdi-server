#!/bin/bash
# Script should be at /usr/sbin, like /usr/sbin/adduser_bi.sh and added to sudouers.
# Example of usage: adduser_bi.sh -u tmp_user -G 'Full user name,,,Vdi-broker' -g vdi-broker-users

read_arguments(){
  # read kerberos settings arguments
  USAGE="VDI setting Kerberos for SSO!
  Usage:
  $(basename "$0") -s service_name, --servicename service_name  -r REALM.NAME, --realm REALM.NAME -i 10.0.0.1, --ip 10.0.0.1, -d domain_zone, --domain domain_zone -k /patch_to_keytab, --keytab /patch_to_keytab [-h, --help]
  
  For disable kerberos use flag --disable"
  
  UNKNOWN=()
  SERVICENAME=""
  REALM=""
  IP=""
  DOMAIN=""
  KEYTAB=""
  
  if [ "$EUID" -ne 0 ]; then
    echo "Script for setting Kerberos must be run as root!"
    exit 1
  fi

  while [[ $# -gt 0 ]]
  do
    KEY="$1"
    case ${KEY} in
        --disable)
        #disable krb in apache
        cp /etc/apache2/sites-available/broker-ssl.conf /etc/apache2/sites-available/broker-ssl.conf.bak
        sed -i '/^.*<Location\ "\/api\/sso\/">/,/^.*<\/Location>.*$/d; /^[[:space:]]$/d' /etc/apache2/sites-available/broker-ssl.conf
        apachectl configtest
        # If an error occurs, then restore the original configuration
        if [ "$?" -ne 0 ]; then
          cp /etc/apache2/sites-available/broker-ssl.conf.bak /etc/apache2/sites-available/broker-ssl.conf
          echo "Error! Operation failed"
          exit 1
        else
          systemctl restart apache2
          systemctl status apache2
          if [ "$?" -eq 0 ]; then
            echo "Kerberos disable!"
            exit 0 
          fi
        fi
        ;;
        -k|--keytab)
        KEYTAB="$2"
        shift # past argument
        shift # past value
        ;;
        -s|--servicename)
        SERVICENAME="$2"
        shift # past argument
        shift # past value
        ;;
        -r|--realm)
        REALM="$2"
        shift # past argument
        shift # past value
        ;;
        -i|--ip)
        IP="$2"
        shift # past argument
        shift # past value
        ;;
        -d|--domain)
        DOMAIN="$2"
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

  if [ -z "${SERVICENAME}" ]; then
    echo "Service name can't be empty." >&2
    exit 1
  fi

  if [ -z "${REALM}" ]; then
    echo "Realm name can't be empty." >&2
    exit 1
  fi

  if [ -z "${IP}" ]; then
    echo "IP adress can't be empty." >&2
    exit 1
  fi

  if [ -z "${DOMAIN}" ]; then
    echo "Domain zone can't be empty." >&2
    exit 1
  fi

  if [ -z "${KEYTAB}" ]; then
    echo "Patch to keytab file can't be empty." >&2
    exit 1
  fi

  if [[ "${SERVICENAME}" != *"@${REALM}" ]]; then
    echo "The service name should be like 'HTTP/astravdi.veil.team@VEIL.TEAM'" >&2
    exit 1
  fi

}

change_apache2_conf(){
    #backup config apache2 config file
    cp /etc/apache2/sites-available/broker-ssl.conf /etc/apache2/sites-available/broker-ssl.conf.bak
    #delete  <Location "/api/sso/"> block in config file
    sed -i '/^.*<Location\ "\/api\/sso\/">/,/^.*<\/Location>.*$/d; /^[[:space:]]$/d' /etc/apache2/sites-available/broker-ssl.conf
    #add <Location "/api/sso/"> block in config file
    
    sed -i "/DocumentRoot\ \/opt\/veil-vdi\/www/a \ \n        <Location \"/api/sso/\">\n                AuthType Kerberos\n                KrbAuthRealms ${REALM}\n                KrbServiceName ${SERVICENAME}\n                Krb5Keytab ${KEYTAB}\n                KrbMethodNegotiate on\n                KrbMethodK5Passwd off\n                require valid-user\n                KrbSaveCredentials on\n                RequestHeader set X-Remote-User expr=%{REMOTE_USER}\n        </Location>" /etc/apache2/sites-available/broker-ssl.conf
}

change_krb5_conf(){
    #backup krb5.conf
    if [ -e /etc/krb5.conf ]
    then
    mv /etc/krb5.conf /etc/krb5.conf.bak
    fi
    #make new kr5.conf
    echo "[logging]
default = FILE:/var/log/krb5libs.log
kdc = FILE:/var/log/krb5kdc.log
admin_server = FILE:/var/log/kadmind.log

[libdefaults]
dns_lookup_realm = false
ticket_lifetime = 24h
renew_lifetime = 7d
forwardable = true
rdns = false
default_realm = ${REALM}
default_ccache_name = KEYRING:persistent:%{uid}

[realms]
${REALM} = {
kdc = ${IP}
admin_server = ${IP}
}

[domain_realm]
.${DOMAIN} = ${REALM}
${DOMAIN} = ${REALM}" > /etc/krb5.conf
}


read_arguments "$@"

change_krb5_conf

change_apache2_conf

apachectl configtest

# If an error occurs, then restore the original configuration
if [ "$?" -ne 0 ]; then
    cp /etc/apache2/sites-available/broker-ssl.conf.bak /etc/apache2/sites-available/broker-ssl.conf
    cp /etc/krb5.conf.bak /etc/krb5.conf
    echo "Error! Operation failed"
else
    systemctl restart apache2
    systemctl status apache2
    if [ "$?" -eq 0 ]; then
        echo "Setup completed successfully! Don't forget to enable SSO in the VDI Broker's Web-interface!"
    fi
fi