cmake_minimum_required(VERSION 3.14)
project(virt_viewer_veil C)

set(CMAKE_C_STANDARD 99)

INCLUDE_DIRECTORIES(
        .
        src
        src/virt_viewer
        src/utility
        src/vdi_client
)

#############################APP FILES#################################
FILE(GLOB SRC_CODE

        config.h

# virt_viewer
        src/virt_viewer/virt-viewer-resources.h
        src/virt_viewer/virt-viewer-resources.c
        src/virt_viewer/virt-viewer-enums.h
        src/virt_viewer/virt-viewer-enums.c
        
        src/virt_viewer/virt-viewer-util.h
        src/virt_viewer/virt-viewer-util.c
        
        src/virt_viewer/virt-viewer-auth.h
        src/virt_viewer/virt-viewer-auth.c
        src/virt_viewer/virt-viewer-app.h
        src/virt_viewer/virt-viewer-app.c
        src/virt_viewer/virt-viewer-file.h
        src/virt_viewer/virt-viewer-file.c
        src/virt_viewer/virt-viewer-session.h
        src/virt_viewer/virt-viewer-session.c
        src/virt_viewer/virt-viewer-display.h
        src/virt_viewer/virt-viewer-display.c
        src/virt_viewer/virt-viewer-notebook.h
        src/virt_viewer/virt-viewer-notebook.c
        src/virt_viewer/virt-viewer-window.h
        src/virt_viewer/virt-viewer-window.c
        src/virt_viewer/virt-viewer-vm-connection.h
        src/virt_viewer/virt-viewer-vm-connection.c
        src/virt_viewer/virt-viewer-display-vte.h
        src/virt_viewer/virt-viewer-display-vte.c
        src/virt_viewer/virt-viewer-timed-revealer.c
        src/virt_viewer/virt-viewer-timed-revealer.h
        #HAVE_SPICE_GTK
        src/virt_viewer/virt-viewer-session-spice.h
        src/virt_viewer/virt-viewer-session-spice.c
        src/virt_viewer/virt-viewer-display-spice.h
        src/virt_viewer/virt-viewer-display-spice.c
        src/virt_viewer/virt-viewer-file-transfer-dialog.h
        src/virt_viewer/virt-viewer-file-transfer-dialog.c
        #remote_viewer_SOURCES
        src/virt_viewer/remote-viewer.h
        src/virt_viewer/remote-viewer.c
        src/virt_viewer/remote-viewer-connect.c
        src/virt_viewer/remote-viewer-connect.h
        src/virt_viewer/remote-viewer-main.c
        #windows-cmdline-wrapper.c
        
#utility
        src/utility/crashhandler.h
        src/utility/crashhandler.c
        
# vdi client
        src/vdi_client/vdi_manager.h
        src/vdi_client/vdi_manager.c
        src/vdi_client/vdi_api_session.h
        src/vdi_client/vdi_api_session.c
        src/vdi_client/vdi_vm_widget.c
        src/vdi_client/vdi_vm_widget.h
)
###############################LIBRARIES###############################
    # GLIB
    find_package(PkgConfig REQUIRED)
    pkg_search_module(GLIB REQUIRED glib-2.0)
    INCLUDE_DIRECTORIES(${GLIB_INCLUDE_DIRS})
    
    # GTK
    PKG_CHECK_MODULES(GTK3 REQUIRED gtk+-3.0)
    INCLUDE_DIRECTORIES(${GTK3_INCLUDE_DIRS})
    SET(LIBS ${LIBS} ${GTK3_LIBRARIES})
    ADD_DEFINITIONS(${GTK3_CFLAGS_OTHER})

if (UNIX)
    # libxml
    INCLUDE_DIRECTORIES(/usr/include/libxml2)
    SET(LIBS ${LIBS} xml2)
    
    # rest 0.7
    INCLUDE_DIRECTORIES(/usr/include/rest-0.7)
    SET(LIBS ${LIBS} rest-0.7)

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

    SET(GUI_TYPE)

endif (UNIX)

if (WIN32)
    # libxml
    INCLUDE_DIRECTORIES(C:/msys64/mingw64/include/libxml2)
    SET(LIBS ${LIBS} xml2)

    # rest 0.7
    INCLUDE_DIRECTORIES(C:/msys64/mingw64/include/rest-0.7)
    SET(LIBS ${LIBS} rest-0.7)

    # SPICE_GTK
    INCLUDE_DIRECTORIES(C:/msys64/mingw64/include/spice-client-gtk-3.0)
    INCLUDE_DIRECTORIES(C:/msys64/mingw64/include/spice-client-glib-2.0)
    INCLUDE_DIRECTORIES(C:/msys64/mingw64/include/spice-1)
    SET(LIBS ${LIBS} spice-client-gtk-3.0 spice-client-glib-2.0)

    # libsoup
    INCLUDE_DIRECTORIES(C:/msys64/mingw64/include/libsoup-2.4)
    SET(LIBS ${LIBS} soup-2.4)

    # json glib
    INCLUDE_DIRECTORIES(C:/msys64/mingw64/include/json-glib-1.0)
    SET(LIBS ${LIBS} json-glib-1.0)

    # other libs
    SET(LIBS ${LIBS}
            m
            -pthread
    )

    SET(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    SET(GUI_TYPE WIN32) # switch off console

endif (WIN32)

#############################LINKING###################################
ADD_EXECUTABLE(virt_viewer_veil WIN32 ${SRC_CODE})
target_link_libraries(
    virt_viewer_veil # exec
    ${LIBS} # libs
)

