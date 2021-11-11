all: deb

fetch:
	wget https://vdi-frontend.tar.xz

deb:
	chmod 775 root/DEBIAN/postinst
	dpkg-deb -b root .

clean:
	@rm -f *.xz *.deb
	@rm -rf root/opt/veil-vdi/thin-client

.PHONY: deb