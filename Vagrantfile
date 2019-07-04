# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# CPU and RAM can be adjusted depending on your system
CPUCOUNT = "2"
RAM = "2048"

def read_config
  require "json"
  file = File.join(File.dirname(__FILE__), "vagrant/config.json")
  file = File.open(file)
  JSON.load(file)
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do | config |
 opts = read_config()
 config.vm.provider "libvirt"
 config.vm.synced_folder '.', '/vagrant', type: "rsync",
   owner: "vagrant", group: "vagrant"

 config.vm.network "private_network", ip: "192.168.20.110"

 config.vm.provision :shell, path: "vagrant/apt_install.sh"
 config.vm.provision :shell, path: "vagrant/init.sh"
 config.vm.provision :shell, path: "vagrant/auth_server.sh", privileged: false
 config.vm.provision :shell, path: "vagrant/vdi_server.sh"
 config.vm.provision :shell, path: "vagrant/frontend.sh", privileged: false

 config.ssh.password = "vagrant"
 config.vm.box_check_update = false

 config.vm.define "vdihost" do | vdihost |
   vdihost.vm.box = opts['boxname']
   vdihost.vm.hostname = opts['hostname']

   vdihost.vm.provider "libvirt" do | libvirt |
     libvirt.memory = "2048"
     libvirt.cpus = 2
   end
 end
end
