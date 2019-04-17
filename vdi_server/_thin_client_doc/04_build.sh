
# http://blog.fidencio.org/2014/11/virt-viewer-using-gtk3-for-windows.html
mingw64-configure --without-libvirtd --without-python  --with-spice-gtk --with-gtk=3.0

make
make -C data/ msi