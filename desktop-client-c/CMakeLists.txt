cmake_minimum_required(VERSION 3.7)
project(thin_client_veil C)

set(CMAKE_C_STANDARD 99)

INCLUDE_DIRECTORIES(
        .
        src
        src/virt_viewer
        src/utility
        src/vdi_client
        src/rdp_viewer
)

#############################APP FILES#################################
FILE(GLOB SRC_CODE

        config.h
        src/remote-viewer.h
        src/remote-viewer.c
        src/remote-viewer-connect.c
        src/remote-viewer-connect.h
        src/remote-viewer-util.h
        src/remote-viewer-util.c
        src/remote-viewer-timed-revealer.c
        src/remote-viewer-timed-revealer.h
        src/remote_viewer_start_settings.h
        src/remote_viewer_start_settings.c
        src/main.c

# virt_viewer
        src/virt_viewer/virt-viewer-resources.h
        src/virt_viewer/virt-viewer-resources.c
        src/virt_viewer/virt-viewer-enums.h
        src/virt_viewer/virt-viewer-enums.c

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
        #HAVE_SPICE_GTK
        src/virt_viewer/virt-viewer-session-spice.h
        src/virt_viewer/virt-viewer-session-spice.c
        src/virt_viewer/virt-viewer-display-spice.h
        src/virt_viewer/virt-viewer-display-spice.c
        src/virt_viewer/virt-viewer-file-transfer-dialog.h
        src/virt_viewer/virt-viewer-file-transfer-dialog.c

#rdp_viewer
        src/rdp_viewer/rdp_viewer.h
        src/rdp_viewer/rdp_viewer.c
        src/rdp_viewer/rdp_channels.h
        src/rdp_viewer/rdp_channels.c
        src/rdp_viewer/rdp_client.h
        src/rdp_viewer/rdp_client.c
        src/rdp_viewer/rdp_cursor.h
        src/rdp_viewer/rdp_cursor.c
        src/rdp_viewer/rdp_display.h
        src/rdp_viewer/rdp_display.c
        
#utility
        src/utility/crashhandler.h
        src/utility/crashhandler.c
        src/utility/jsonhandler.h
        src/utility/jsonhandler.c
        src/utility/settingsfile.c
        src/utility/settingsfile.h
        src/utility/async.h
        src/utility/async.c
        
# vdi client
        src/vdi_client/vdi_manager.h
        src/vdi_client/vdi_manager.c
        src/vdi_client/vdi_api_session.h
        src/vdi_client/vdi_api_session.c
        src/vdi_client/vdi_pool_widget.h
        src/vdi_client/vdi_pool_widget.c
        src/vdi_client/vdi_ws_client.h
        src/vdi_client/vdi_ws_client.c
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
    SET(LIBS_INCLUDE_PATH /usr/include/)

    # freerdp
    INCLUDE_DIRECTORIES(${LIBS_INCLUDE_PATH}freerdp2)
    SET(LIBS ${LIBS} freerdp2 freerdp-client2)

    # winpr2
    INCLUDE_DIRECTORIES(${LIBS_INCLUDE_PATH}winpr2)
    SET(LIBS ${LIBS} winpr2 winpr-tools2)

    # other libs
    SET(LIBS ${LIBS}
            m
            -rdynamic
            -pthread
            -lX11
    )

    SET(GUI_TYPE)

endif (UNIX)

if (WIN32)
    SET(LIBS_INCLUDE_PATH C:/msys64/mingw64/include/)

    # freerdp
    SET(FREERDP_PATH C:/job/freerdp/FreeRDP-2.0.0-rc4/FreeRDP-2.0.0-rc4/)
    INCLUDE_DIRECTORIES(${FREERDP_PATH}include)
    SET(LIBS ${LIBS} ${FREERDP_PATH}Release/freerdp2.lib)
    SET(LIBS ${LIBS} ${FREERDP_PATH}Release/freerdp-client2.lib)

    # winpr2
    INCLUDE_DIRECTORIES(${FREERDP_PATH}winpr/include)
    SET(LIBS ${LIBS} ${FREERDP_PATH}Release/winpr-tools2.lib)
    SET(LIBS ${LIBS} ${FREERDP_PATH}Release/winpr2.lib)

    # other libs
    SET(LIBS ${LIBS}
            m
            -pthread
    )

    SET(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    SET(GUI_TYPE WIN32) # switch off console

endif (WIN32)

    # libxml
    INCLUDE_DIRECTORIES(${LIBS_INCLUDE_PATH}libxml2)
    SET(LIBS ${LIBS} xml2)

    # SPICE_GTK
    INCLUDE_DIRECTORIES(${LIBS_INCLUDE_PATH}spice-client-gtk-3.0)
    INCLUDE_DIRECTORIES(${LIBS_INCLUDE_PATH}spice-client-glib-2.0)
    INCLUDE_DIRECTORIES(${LIBS_INCLUDE_PATH}spice-1)
    SET(LIBS ${LIBS} spice-client-gtk-3.0 spice-client-glib-2.0)

    # libsoup
    INCLUDE_DIRECTORIES(${LIBS_INCLUDE_PATH}libsoup-2.4)
    SET(LIBS ${LIBS} soup-2.4)

    # json glib
    INCLUDE_DIRECTORIES(${LIBS_INCLUDE_PATH}json-glib-1.0)
    SET(LIBS ${LIBS} json-glib-1.0)

#############################LINKING###################################
ADD_EXECUTABLE(thin_client_veil ${GUI_TYPE} ${SRC_CODE})
target_link_libraries(
    thin_client_veil # exec
    ${LIBS} # libs
)
