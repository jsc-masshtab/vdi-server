all: deb

fetch:
	wget https://vdi-docs.tar.xz

deb:
	dpkg-deb -b root .

clean:
	@rm -f *.xz *.deb
	@rm -rf root/opt/veil-vdi/docs
	@mkdir -p root/opt/veil-vdi/docs

.PHONY: deb