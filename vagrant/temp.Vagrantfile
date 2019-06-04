# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# CPU and RAM can be adjusted depending on your system
CPUCOUNT = "2"
RAM = "2048"



Vagrant.configure(VAGRANTFILE_API_VERSION) do | config |
  config.vm.provider "libvirt"
  config.vm.provision "shell", inline: $script

  config.ssh.password = "vagrant"

  config.vm.define "vdihost" do | vdihost |
    vdihost.vm.box = $boxname
    vdihost.vm.hostname = "vdihost"

    vdihost.vm.provider "libvirt" do | libvirt |
      libvirt.memory = "2048"
      libvirt.cpus = 2
    end
  end
end
