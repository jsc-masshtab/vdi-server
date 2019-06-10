NULL =

ACLOCAL_AMFLAGS = -I m4

SUBDIRS = icons src man po data tests

AM_DISTCHECK_CONFIGURE_FLAGS = --disable-update-mimedb
EXTRA_DIST =					\
	$(PACKAGE).spec	$(PACKAGE).spec.in	\
	mingw-$(PACKAGE).spec.in		\
	intltool-extract.in			\
	intltool-merge.in			\
	intltool-update.in			\
	GNUmakefile				\
	maint.mk				\
	cfg.mk					\
	build-aux/gitlog-to-changelog		\
	build-aux/useless-if-before-free	\
	build-aux/vc-list-files			\
	AUTHORS.in				\
	README.md				\
	$(NULL)

DISTCLEAN_FILES =				\
	$(PACKAGE).spec				\
	mingw-$(PACKAGE).spec			\
	intltool-extract			\
	intltool-merge				\
	intltool-update				\
	$(NULL)

MAINTAINERCLEANFILES =				\
	$(srcdir)/AUTHORS			\
	$(srcdir)/INSTALL			\
	$(GITIGNORE_MAINTAINERCLEANFILES_TOPLEVEL)	\
	$(GITIGNORE_MAINTAINERCLEANFILES_M4_LIBTOOL)	\
	$(srcdir)/m4/intltool.m4		\
	$(NULL)

dist-hook: gen-ChangeLog gen-AUTHORS

# Generate the ChangeLog file (with all entries since the switch to git)
# and insert it into the directory we're about to use to create a tarball.
if OS_WIN32
.PHONY: gen-ChangeLog gen-AUTHORS msi
else
.PHONY: gen-ChangeLog gen-AUTHORS
endif

gen-ChangeLog:
	if test -d .git || test -d ../.git; then		\
	  $(top_srcdir)/build-aux/gitlog-to-changelog		\
	    > $(distdir)/cl-t;					\
	  rm -f $(distdir)/ChangeLog;				\
	  mv $(distdir)/cl-t $(distdir)/ChangeLog;		\
	fi

gen-AUTHORS:
	$(AM_V_GEN)if test -d $(srcdir)/.git; then                      \
	   out="`cd $(srcdir) && git log --pretty=format:'%aN <%aE>' | sort -u`" && \
	   perl -p -e "s/#authorslist#// and print '$$out'"            \
	     < $(srcdir)/AUTHORS.in > $(distdir)/AUTHORS-tmp &&        \
	   mv -f $(distdir)/AUTHORS-tmp $(distdir)/AUTHORS ;           \
	fi

if OS_WIN32
.PHONY: msi
msi:
	make -C $(builddir)/data msi
endif


# this make sure those files are regenerated when they change
# (in maintainer-mode)
all-local: virt-viewer.spec mingw-virt-viewer.spec

-include $(top_srcdir)/git.mk
