NULL =

dist_man_MANS =					\
	remote-viewer.1				\
	virt-viewer.1				\
	$(NULL)

EXTRA_DIST =					\
	remote-viewer.pod			\
	virt-viewer.pod				\
	$(NULL)

MAINTAINERCLEANFILES = $(dist_man_MANS)

%.1: %.pod
	$(AM_V_GEN)pod2man -c "Virtualization Support" $< > $@

-include $(top_srcdir)/git.mk
