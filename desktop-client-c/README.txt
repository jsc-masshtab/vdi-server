Veil VDI Thin Cleint

Build checked on Ubuntu 18.04, CentOS 7, Windows 7.

======================================================Building on Linux===================================================
1)Install followwing packages:
sudo apt install spice-client-gtk
sudo apt install libspice-gtk-3.0-dev
sudo apt install libjson-glib-dev
sudo apt install libxml2-dev

2)Open terminal in desktop-client-c directory and execute commands:
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ../
make 


======================================================Building on Windows==================================================

1) MSYS2 installation

The MSYS2 project provides a UNIX-like development environment for Windows. It provides packages for many software applications and libraries, including the GTK stack. If you prefer developing using Visual Studio, you may be better off installing GTK from vcpkg instead.

In MSYS2 packages are installed using the pacman package manager.

Note: in the following steps, we will assume you're using a 64-bit Windows. Therefore, the package names include the x86_64 architecture identifier. If you're using a 32-bit Windows, please adapt the instructions below using the i686 architecture identifier.
Step 1: Install MSYS2

Download the MSYS2 installer that matches your platform and follow the installation instructions.
Step 2: Install GTK3 and its dependencies

Open a MSYS2 shell, and run:
pacman -S mingw-w64-x86_64-gtk3
Step 3 (recommended): Install GTK core applications

Glade is a GUI designer for GTK. It lets you design your GUI and export it in XML format. You can then import your GUI from your code using the GtkBuilder API. Read the GtkBuilder section in the GTK manual for more information.

To install Glade:
pacman -S mingw-w64-x86_64-glade

Devhelp is a help browser. It lets you easily navigate offline in the GTK, glib and gobject API help relative to the version of these libraries installed on your system.

To install Devhelp:
pacman -S mingw-w64-x86_64-devhelp

Step 4 (optional): Install build tools

pacman -S mingw-w64-x86_64-toolchain base-devel 


2) In file CmaleLists.txt in variable LIBS_INCLUDE_PATH set the path to MSYS_INCLUDE

3) Install Clion

4) In Clion open CmakeListx.txt and build the project  


======================================================INSTALL AND LAUNCH==========================================
On Windows unpack archive vdi_client_release_win7.zip and just launch executable file
On Linux unpack archive vdi_client_release_Ubuntu_18_04_2_LTS.tar.xz and execute script start_vdi_client.sh

 
