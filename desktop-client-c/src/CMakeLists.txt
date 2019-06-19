cmake_minimum_required(VERSION 3.14)
project(virt_viewer_veil C)

set(CMAKE_C_STANDARD 99)

INCLUDE_DIRECTORIES(
../
)

#############################APP FILES#################################
FILE(GLOB SRC_CODE
#BUILT_SOURCES
virt-viewer-resources.h
virt-viewer-resources.c
virt-viewer-enums.h
virt-viewer-enums.c
#libvirt_viewer_util_la_SOURCES
virt-viewer-util.h
virt-viewer-util.c
#libvirt_viewer_la_SOURCES
virt-viewer-auth.h
virt-viewer-auth.c
virt-viewer-app.h
virt-viewer-app.c
virt-viewer-file.h
virt-viewer-file.c
virt-viewer-session.h
virt-viewer-session.c
virt-viewer-display.h
virt-viewer-display.c
virt-viewer-notebook.h
virt-viewer-notebook.c
virt-viewer-window.h
virt-viewer-window.c
virt-viewer-vm-connection.h
virt-viewer-vm-connection.c
virt-viewer-display-vte.h
virt-viewer-display-vte.c
virt-viewer-timed-revealer.c
virt-viewer-timed-revealer.h

#HAVE_GTK_VNC
#virt-viewer-session-vnc.h
#virt-viewer-session-vnc.c
#virt-viewer-display-vnc.h
#virt-viewer-display-vnc.c
#HAVE_SPICE_GTK
virt-viewer-session-spice.h
virt-viewer-session-spice.c
virt-viewer-display-spice.h
virt-viewer-display-spice.c
virt-viewer-file-transfer-dialog.h
virt-viewer-file-transfer-dialog.c
#HAVE_OVIRT
ovirt-foreign-menu.h
ovirt-foreign-menu.c
remote-viewer-iso-list-dialog.c
remote-viewer-iso-list-dialog.h

#remote_viewer_SOURCES
remote-viewer.h
remote-viewer.c
remote-viewer-connect.c
remote-viewer-connect.h
remote-viewer-main.c

crashhandler.h
crashhandler.c

../config.h

# vdi related
vdi_manager.h
vdi_manager.c
vdi_api_session.h
vdi_api_session.c
vdi_vm_widget.c
vdi_vm_widget.h

#windows-cmdline-wrapper.c

)
###############################LIBRARIES###############################
# GLIB
find_package(PkgConfig REQUIRED)
pkg_search_module(GLIB REQUIRED glib-2.0)
INCLUDE_DIRECTORIES(${GLIB_INCLUDE_DIRS})
INCLUDE_DIRECTORIES(/usr/include/glib-2.0/gio)
SET(LIBS ${LIBS} ${GLIB_LDFLAGS})

# GTK
PKG_CHECK_MODULES(GTK3 REQUIRED gtk+-3.0)
INCLUDE_DIRECTORIES(${GTK3_INCLUDE_DIRS})
#link_directories(${GTK3_LIBRARY_DIRS})
SET(LIBS ${LIBS} ${GTK3_LIBRARIES})
ADD_DEFINITIONS(${GTK3_CFLAGS_OTHER})

# libvirt-glib sudo apt install libvirt-glib-1.0
#INCLUDE_DIRECTORIES(/usr/include/libvirt-glib-1.0)
#SET(LIBS ${LIBS} virt-glib-1.0 virt)

# libxml
INCLUDE_DIRECTORIES(/usr/include/libxml2)
SET(LIBS ${LIBS} xml2)

# rest 0.7
INCLUDE_DIRECTORIES(/usr/include/rest-0.7)
SET(LIBS ${LIBS} rest-0.7)

# govirt  sudo apt install gir1.2-govirt-1.0 libgovirt-dev
INCLUDE_DIRECTORIES(/usr/include/govirt-1.0)
SET(LIBS ${LIBS} govirt)

# SPICE_GTK sudo apt install spice-client-gtk
# sudo apt install libspice-gtk-3.0-dev
INCLUDE_DIRECTORIES(/usr/include/spice-client-gtk-3.0)
INCLUDE_DIRECTORIES(/usr/include/spice-client-glib-2.0)
INCLUDE_DIRECTORIES(/usr/include/spice-1)
INCLUDE_DIRECTORIES(/usr/include/spice-controller)
SET(LIBS ${LIBS} spice-client-gtk-3.0 spice-client-glib-2.0 spice-controller)

# libsoup
INCLUDE_DIRECTORIES(/usr/include/libsoup-2.4)
SET(LIBS ${LIBS} soup-2.4)

# json glib
INCLUDE_DIRECTORIES(/usr/include/json-glib-1.0)
SET(LIBS ${LIBS} json-glib-1.0)

# other libs
SET(LIBS ${LIBS}
        m
        #gio-2.0
        #gobject-2.0
        -rdynamic
        -pthread
)

#############################LINKING###################################
ADD_EXECUTABLE(virt_viewer_veil  ${SRC_CODE})
target_link_libraries(
    virt_viewer_veil # exec
    ${LIBS} # libs
)

