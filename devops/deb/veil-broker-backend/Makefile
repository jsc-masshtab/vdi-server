all: deb

fetch:
	wget https://vdi-backend.tar.xz

deb:
	chmod 775 root/DEBIAN/postinst
	dpkg-deb -b root .

clean:
	@rm -f *.xz *.deb
	@rm -rf root/opt/veil-vdi/app
	@mkdir -p root/opt/veil-vdi/app

.PHONY: deb
