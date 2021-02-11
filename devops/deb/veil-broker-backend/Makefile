all: deb

fetch:
	wget https://vdi-backend.tar.xz

deb:
	chown -R root:root root
	chmod 775 root/DEBIAN/postinst
	chmod 440 root/etc/sudoers.d/vdiadmin
	chmod +x root/usr/sbin/vdi_*
	dpkg-deb -b root .

clean:
	@rm -f *.xz *.deb
	@rm -rf root/opt/veil-vdi/app
	@mkdir -p root/opt/veil-vdi/app

.PHONY: deb
