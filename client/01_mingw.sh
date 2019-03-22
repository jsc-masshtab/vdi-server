$ sudo yum -y install dh-autoreconf.noarch
$ sudo yum -y install gtk-doc.noarch
$ sudo yum -y install icoutils.x86_64
$ sudo yum -y install perl-Text-CSV.noarch
$ sudo yum -y install vala-tools.x86_64
$ sudo yum -y install msitools.x86_64
### spice-common编译报错recipe for target 'generated_client_demarshallers.c' failed
$ sudo pip install pyparsing
### 64位virt-viewer编译依赖包
$ sudo yum -y install mingw64-filesystem.noarch
$ sudo yum -y install mingw64-gcc.x86_64
$ sudo yum -y install mingw64-libxml2.noarch
$ sudo yum -y install mingw64-glib2.noarch
$ sudo yum -y install mingw64-pixman.noarch
$ sudo yum -y install mingw64-openssl.noarch
$ sudo yum -y install mingw64-gtk3.noarch
$ sudo yum -y install mingw64-gstreamer*
$ sudo yum -y install mingw64-celt051.noarch
$ sudo yum -y install mingw64-gdb.noarch

$ dnf builddep mingw-virt-viewer.spec
