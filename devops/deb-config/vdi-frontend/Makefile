all: deb

fetch:
	wget https://vdi-frontend.tar.xz

deb:
	dpkg-deb -b root .

clean:
	@rm -f *.xz *.deb
	@rm -rf root/opt/veil-vdi/www
	@mkdir -p root/opt/veil-vdi/www

.PHONY: deb
