# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# Software version variables
GOVERSION = "1.11.5"
UBUNTUVERSION = "18.04"

# CPU and RAM can be adjusted depending on your system
CPUCOUNT = "2"
RAM = "4096"

$script = <<SCRIPT

# Get the ARCH
ARCH="$(uname -m | sed 's|i686|386|' | sed 's|x86_64|amd64|')"

# Install Prereq Packages
export DEBIAN_PRIORITY=critical
export DEBIAN_FRONTEND=noninteractive
export DEBCONF_NONINTERACTIVE_SEEN=true
APT_OPTS="--assume-yes --no-install-suggests --no-install-recommends -o Dpkg::Options::=\"--force-confdef\" -o Dpkg::Options::=\"--force-confold\""
echo "Upgrading packages ..."
apt-get update ${APT_OPTS} >/dev/null
apt-get upgrade ${APT_OPTS} >/dev/null
echo "Installing prerequisites ..."
apt-get install ${APT_OPTS} build-essential curl git pipenv >/dev/null

git clone git@gitlab.bazalt.team:vdi/vdiserver.git
cd vdiserver
pipenv install && pipenv run uvicorn vdi.app:app


SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "generic/debian10"
  config.vm.hostname = "vdihost"

  config.vm.provision "prepare-shell", type: "shell", inline: "sudo sed -i '/tty/!s/mesg n/tty -s \\&\\& mesg n/' /root/.profile", privileged: false
  config.vm.provision "initial-setup", type: "shell", inline: $script
#   config.vm.synced_folder '.', '/opt/gopath/src/github.com/hashicorp/terraform'


end
