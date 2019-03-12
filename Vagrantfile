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

# Install Prereq Packages
export DEBIAN_PRIORITY=critical
export DEBIAN_FRONTEND=noninteractive
export DEBCONF_NONINTERACTIVE_SEEN=true
APT_OPTS="--assume-yes --no-install-suggests --no-install-recommends"
echo "Upgrading packages ..."
apt-get update ${APT_OPTS} >/dev/null
apt-get upgrade ${APT_OPTS} >/dev/null
echo "Installing prerequisites ..."
apt-get install ${APT_OPTS} build-essential curl python3-dev python3-pip > /dev/null
apt-get install ${APT_OPTS} nginx

echo "Installing pipenv..."
python3 -m pip install pipenv


echo "Pipenv"

export PIPENV_SKIP_LOCK=1

cd /vagrant

pipenv install
pipenv run uvicorn vdi.app:app


SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do | config |
 config.vm.provider "libvirt" 
 config.vm.synced_folder '.', '/vagrant'

 config.vm.define "vdihost" do | vdihost |
   vdihost.vm.box = "generic/debian10"
   vdihost.vm.hostname = "vdihost"
   vdihost.vm.provision "initial-setup", type: "shell", inline: $script

   vdihost.vm.network :forwarded_port, guest: 80, host: 8888, host_ip: "127.0.0.1"
   vdihost.vm.network :forwarded_port, guest: 8000, host: 8000, host_ip: "127.0.0.1"
   vdihost.vm.network :forwarded_port, guest: 8001, host: 8001, host_ip: "127.0.0.1"
 
   vdihost.vm.provider "libvirt" do | libvirt |
     libvirt.memory = "2048"
     libvirt.cpus = 2
     libvirt.nested = true
     libvirt.volume_cache = 'writeback'
   end
 end
end

