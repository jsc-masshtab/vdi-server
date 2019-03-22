
mingw64-configure --without-libvirtd --without-python  --with-spice-gtk --with-gtk=3.0

make
make -C data/ msi