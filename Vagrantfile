# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# CPU and RAM can be adjusted depending on your system
CPUCOUNT = "2"
RAM = "2048"


Vagrant.configure(VAGRANTFILE_API_VERSION) do | config |
 config.vm.provider "libvirt"
 #config.vm.synced_folder '.', '/vagrant', type: "nfs", mount_options: ["vers=3,tcp"]
 config.vm.synced_folder '.', '/vagrant', type: "rsync",
   owner: "vagrant", group: "vagrant"
 config.vm.network "private_network", ip: "192.168.20.110"
 config.vm.provision :shell, path: "vagrant/init.sh"
 config.vm.provision :shell, path: "vagrant/vdi_server.sh"
 config.vm.provision :shell, path: "vagrant/auth_server.sh", privileged: false
 config.vm.provision :shell, path: "vagrant/frontend.sh", privileged: false

 config.vm.define "vdihost" do | vdihost |
   vdihost.vm.box = "archlinux/archlinux"
   vdihost.vm.hostname = "vdihost"

   vdihost.vm.provider "libvirt" do | libvirt |
     libvirt.memory = "2048"
     libvirt.cpus = 2
   end
 end
end
