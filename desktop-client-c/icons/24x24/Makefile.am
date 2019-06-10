EXTRA_DIST =
size = $(notdir $(PWD))

apps_icondir = $(datadir)/icons/hicolor/$(size)/apps/
apps_icon_DATA = $(PACKAGE).png
EXTRA_DIST += $(apps_icon_DATA)

devices_icondir = $(datadir)/icons/hicolor/$(size)/devices/
devices_icon_DATA = virt-viewer-usb.png virt-viewer-usb.svg
EXTRA_DIST += $(devices_icon_DATA)

-include $(top_srcdir)/git.mk
