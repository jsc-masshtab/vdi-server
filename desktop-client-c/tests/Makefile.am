NULL =

AM_CPPFLAGS = \
	-DLOCALE_DIR=\""$(datadir)/locale"\" \
	-DG_LOG_DOMAIN=\"virt-viewer\" \
	-I$(top_builddir)/src/ \
	-I$(top_srcdir)/src/ \
	-I$(top_srcdir)/tests/ \
	$(GLIB2_CFLAGS) \
	$(GTK_CFLAGS) \
	$(WARN_CFLAGS) \
	$(NULL)

LDADD= \
	$(top_builddir)/src/libvirt-viewer-util.la \
	$(GLIB2_LIBS) \
	$(GTK_LIBS) \
	$(LIBXML2_LIBS) \
	$(NULL)

TESTS = test-version-compare test-monitor-mapping test-hotkeys test-monitor-alignment
check_PROGRAMS = $(TESTS)
test_version_compare_SOURCES = \
	test-version-compare.c \
	$(NULL)

test_monitor_mapping_SOURCES = \
	test-monitor-mapping.c \
	$(NULL)

test_hotkeys_SOURCES = \
	test-hotkeys.c \
	$(NULL)

test_hotkeys_LDADD = \
	$(top_builddir)/src/libvirt-viewer.la \
	$(LDADD) \
	$(NULL)

test_monitor_alignment_SOURCES = \
	test-monitor-alignment.c \
	$(NULL)

if OS_WIN32
TESTS += redirect-test
redirect_test_SOURCES = redirect-test.c
redirect_test_LDFLAGS = -Wl,--subsystem,windows
redirect_test_CPPFLAGS = $(GLIB2_CFLAGS)
endif

-include $(top_srcdir)/git.mk
