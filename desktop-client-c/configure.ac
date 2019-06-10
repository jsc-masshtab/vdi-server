
AC_INIT([virt-viewer],[6.0])
AC_CONFIG_SRCDIR(src/virt-viewer-main.c)
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_AUX_DIR([build-aux])
AC_CONFIG_HEADERS([config.h])
dnl Make automake keep quiet about wildcards & other GNUmake-isms
AM_INIT_AUTOMAKE([subdir-objects -Wno-portability foreign])
AC_CANONICAL_HOST

# Use the silent-rules feature when possible.
m4_ifndef([AM_SILENT_RULES], [m4_define([AM_SILENT_RULES],[])])
AM_SILENT_RULES([yes])

# Keep these two definitions in agreement.
GLIB2_REQUIRED="2.38"
GLIB2_ENCODED_VERSION="GLIB_VERSION_2_38"

# Keep these two definitions in agreement.
GTK_REQUIRED="3.12"
GTK_ENCODED_VERSION="GDK_VERSION_3_12"

LIBXML2_REQUIRED="2.6.0"
LIBVIRT_REQUIRED="0.10.0"
LIBVIRT_GLIB_REQUIRED="0.1.8"
GTK_VNC_REQUIRED="0.4.0"
SPICE_GTK_REQUIRED="0.33"
SPICE_PROTOCOL_REQUIRED="0.12.7"
GOVIRT_REQUIRED="0.3.2"

AC_SUBST([GLIB2_REQUIRED])
AC_SUBST([LIBXML2_REQUIRED])
AC_SUBST([LIBVIRT_REQUIRED])
AC_SUBST([LIBVIRT_GLIB_REQUIRED])
AC_SUBST([GTK_REQUIRED])
AC_SUBST([GTK_VNC_REQUIRED])
AC_SUBST([SPICE_GTK_REQUIRED])
AC_SUBST([SPICE_PROTOCOL_REQUIRED])
AC_SUBST([GOVIRT_REQUIRED])

AC_MSG_CHECKING([for native Win32])
case "$host_os" in
     *mingw*|*cygwin*)
        os_win32=yes
        case "$host" in
            amd64*|x86_64*)
                WIXL_ARCH="x64"
            ;;
            *)
                WIXL_ARCH="x86"
            ;;
        esac
        AC_SUBST(WIXL_ARCH)
        ;;
     *)
        os_win32=no
        ;;
esac
AC_MSG_RESULT([$os_win32])
AM_CONDITIONAL([OS_WIN32],[test "$os_win32" = "yes"])

AC_PROG_CC
AM_PROG_CC_C_O
LT_INIT

AC_CHECK_PROGS(ICOTOOL, [icotool], [icotool])

AS_IF([test "x$os_win32" = "xyes"], [
     AC_CHECK_TOOL(WINDRES, [windres])

     if test -z "$WINDRES" ; then
       AC_MSG_ERROR("windres is required to compile virt-viewer on this platform")
     fi
])

AC_CONFIG_LIBOBJ_DIR([src])

AC_DEFINE([_GNU_SOURCE], [], [Enable GNU extensions])

# Autoconf 2.61a.99 and earlier don't support linking a file only
# in VPATH builds.  But since GNUmakefile is for maintainer use
# only, it does not matter if we skip the link with older autoconf.
# Automake 1.10.1 and earlier try to remove GNUmakefile in non-VPATH
# builds, so use a shell variable to bypass this.
GNUmakefile=GNUmakefile
m4_if(m4_version_compare([2.61a.100],
        m4_defn([m4_PACKAGE_VERSION])), [1], [],
      [AC_CONFIG_LINKS([$GNUmakefile:$GNUmakefile], [],
        [GNUmakefile=$GNUmakefile])])

VIRT_VIEWER_COMPILE_WARNINGS(maximum)

GETTEXT_PACKAGE=virt-viewer
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE],"$GETTEXT_PACKAGE", [GETTEXT package name])

AM_GLIB_GNU_GETTEXT
IT_PROG_INTLTOOL([0.35.0])

PKG_PROG_PKG_CONFIG
GLIB_MKENUMS=`$PKG_CONFIG --variable=glib_mkenums glib-2.0`
AC_SUBST(GLIB_MKENUMS)

PKG_CHECK_MODULES(GLIB2, glib-2.0 >= $GLIB2_REQUIRED gio-2.0 gthread-2.0 gmodule-export-2.0)
GLIB2_CFLAGS="$GLIB2_CFLAGS -DGLIB_VERSION_MIN_REQUIRED=$GLIB2_ENCODED_VERSION \
    -DGLIB_VERSION_MAX_ALLOWED=$GLIB2_ENCODED_VERSION"
AC_SUBST(GLIB2_CFLAGS)

AC_ARG_VAR([GLIB_COMPILE_RESOURCES],[the glib-compile-resources program])
AC_PATH_PROG([GLIB_COMPILE_RESOURCES],[glib-compile-resources],[])
if test -z "$GLIB_COMPILE_RESOURCES"; then
  AC_MSG_ERROR([glib-compile-resources not found])
fi

PKG_CHECK_MODULES(LIBXML2, libxml-2.0 >= $LIBXML2_REQUIRED)

AC_ARG_WITH([libvirt],
    AS_HELP_STRING([--without-libvirt], [Ignore presence of libvirt and disable it]))

AS_IF([test "x$with_libvirt" != "xno" && test "x$with_libvirt" != "xyes"],
      [PKG_CHECK_EXISTS([libvirt >= $LIBVIRT_REQUIRED],
                        [with_libvirt=yes], [with_libvirt=no])])

AS_IF([test "x$with_libvirt" = "xyes"],
      [PKG_CHECK_MODULES(LIBVIRT, [libvirt >= $LIBVIRT_REQUIRED] [libvirt-glib-1.0 >= $LIBVIRT_GLIB_REQUIRED])]
      [AC_DEFINE([HAVE_LIBVIRT], 1, [Have libvirt?])]
)
AM_CONDITIONAL([HAVE_LIBVIRT], [test "x$with_libvirt" = "xyes"])

old_LIBS=$LIBS
LIBS=$LIBVIRT_LIBS
# virDomainOpenGraphicsFD was introduced in libvirt 1.2.8
AC_CHECK_LIB([virt],
             [virDomainOpenGraphicsFD],
             [AC_DEFINE([HAVE_VIR_DOMAIN_OPEN_GRAPHICS_FD], 1, [Have virDomainOpenGraphicsFD?])])
LIBS=$old_LIBS

PKG_CHECK_MODULES(GTK, gtk+-3.0 >= $GTK_REQUIRED)
GTK_CFLAGS="$GTK_CFLAGS -DGDK_VERSION_MIN_REQUIRED=$GTK_ENCODED_VERSION \
    -DGDK_VERSION_MAX_ALLOWED=$GTK_ENCODED_VERSION"
AC_SUBST(GTK_CFLAGS)

AC_ARG_WITH([gtk-vnc],
    AS_HELP_STRING([--without-gtk-vnc], [Ignore presence of gtk-vnc and disable it]))

AS_IF([test "x$with_gtk_vnc" != "xno" && test "x$with_gtk_vnc" != "xyes"],
      [PKG_CHECK_EXISTS([gtk-vnc-2.0 >= $GTK_VNC_REQUIRED],
                        [with_gtk_vnc=yes], [with_gtk_vnc=no])])

AS_IF([test "x$with_gtk_vnc" = "xyes"],
      [PKG_CHECK_MODULES(GTK_VNC, [gtk-vnc-2.0 >= $GTK_VNC_REQUIRED])]
      [AC_DEFINE([HAVE_GTK_VNC], 1, [Have gtk-vnc?])]
)
AM_CONDITIONAL([HAVE_GTK_VNC], [test "x$with_gtk_vnc" = "xyes"])

AC_ARG_WITH([spice-gtk],
    AS_HELP_STRING([--without-spice-gtk], [Ignore presence of spice-gtk and disable it]))

AS_IF([test "x$with_spice_gtk" != "xno" && test "x$with_spice_gtk" != "xyes"],
      [PKG_CHECK_EXISTS([spice-client-gtk-3.0 >= $SPICE_GTK_REQUIRED
                         spice-client-glib-2.0 >= $SPICE_GTK_REQUIRED
                         spice-controller spice-protocol >= $SPICE_PROTOCOL_REQUIRED],
                        [with_spice_gtk=yes], [with_spice_gtk=no])])

AS_IF([test "x$with_spice_gtk" = "xyes"],
      [PKG_CHECK_MODULES(SPICE_GTK, [spice-client-gtk-3.0 >= $SPICE_GTK_REQUIRED
                                     spice-client-glib-2.0 >= $SPICE_GTK_REQUIRED])]
      [PKG_CHECK_MODULES(SPICE_CONTROLLER, [spice-controller])]
      [PKG_CHECK_MODULES(SPICE_PROTOCOL, [spice-protocol >= $SPICE_PROTOCOL_REQUIRED])]
      [AC_DEFINE([HAVE_SPICE_GTK], 1, [Have spice-gtk?])]
)
AM_CONDITIONAL([HAVE_SPICE_GTK], [test "x$with_spice_gtk" = "xyes"])

AC_ARG_WITH([ovirt],
    AS_HELP_STRING([--without-ovirt], [Ignore presence of librest and disable oVirt support]))

AS_IF([test "x$with_ovirt" != "xno" && test "x$with_ovirt" != "xyes"],
      [PKG_CHECK_EXISTS([govirt-1.0 >= $GOVIRT_REQUIRED],
                        [with_ovirt=yes], [with_ovirt=no])])

AS_IF([test "x$with_ovirt" = "xyes"],
      [PKG_CHECK_MODULES([OVIRT], [govirt-1.0 >= $GOVIRT_REQUIRED])]
      [AC_DEFINE([HAVE_OVIRT], 1, [Have libgovirt?])]
      [SAVED_CFLAGS="$CFLAGS"
       SAVED_LIBS="$LIBS"
       CFLAGS="$OVIRT_CFLAGS"
       LIBS="$OVIRT_LIBS"
       AC_COMPILE_IFELSE([AC_LANG_PROGRAM([[#include <govirt/govirt.h>]],
        [static int err = OVIRT_REST_CALL_ERROR_CANCELLED;
         void *fun = rest_proxy_auth_cancel;])],
        [AC_DEFINE([HAVE_OVIRT_CANCEL], 1, [Have rest_proxy_auth_cancel and OVIRT_REST_CALL_ERROR_CANCELLED?])],
        [])
       CFLAGS="$SAVED_CFLAGS"
       LIBS="$SAVED_LIBS"]
)
AM_CONDITIONAL([HAVE_OVIRT], [test "x$with_ovirt" = "xyes"])

dnl Decide if this platform can support the SSH tunnel feature.
AC_CHECK_HEADERS([sys/socket.h sys/un.h windows.h])
AC_CHECK_FUNCS([fork socketpair])


if test "x$with_gtk_vnc" != "xyes" && test "x$with_spice_gtk" != "xyes"; then
    AC_MSG_ERROR([At least one of spice or vnc must be used])
fi

AC_ARG_WITH([osid],
    AS_HELP_STRING([--with-osid=id], [Set OS ID for use in .vv files]))
if test -n "$with_osid"; then
    AC_DEFINE_UNQUOTED([REMOTE_VIEWER_OS_ID], "$with_osid", [OS ID for this build])
fi

AC_ARG_WITH([buildid],
    AS_HELP_STRING([--with-buildid=id], [Set additional build version details]),
    [buildid="$with_buildid"], [buildid="0"])

if test "x$buildid" != "x0"; then
    AC_DEFINE_UNQUOTED([BUILDID], "-$buildid", [Build version details])
    AC_SUBST([BUILDID], "-$buildid")
else
    AC_DEFINE_UNQUOTED([BUILDID], "", [Build version details])
fi

major=`echo $PACKAGE_VERSION | cut -d. -f1`
minor=`echo $PACKAGE_VERSION | cut -d. -f2`
WINDOWS_PRODUCTVERSION="$major.$minor.$buildid"
AC_SUBST([WINDOWS_PRODUCTVERSION])


AC_PATH_PROG(UPDATE_MIME_DATABASE, update-mime-database, no)

AC_ARG_ENABLE(update-mimedb,
   AS_HELP_STRING([--disable-update-mimedb],
                   [disable the update-mime-database after install [default=no]]),,
    enable_update_mimedb=yes)
AM_CONDITIONAL(ENABLE_UPDATE_MIMEDB, test x$enable_update_mimedb = xyes)


AC_CONFIG_FILES([
    Makefile
    data/Makefile
    data/virt-viewer.wxs
    icons/Makefile
    icons/16x16/Makefile
    icons/22x22/Makefile
    icons/24x24/Makefile
    icons/32x32/Makefile
    icons/48x48/Makefile
    icons/256x256/Makefile
    man/Makefile
    mingw-virt-viewer.spec
    po/Makefile.in
    src/Makefile
    src/virt-viewer.rc
    tests/Makefile
    virt-viewer.spec
])
AC_OUTPUT

AC_MSG_NOTICE([])
AC_MSG_NOTICE([Configuration summary])
AC_MSG_NOTICE([=====================])
AC_MSG_NOTICE([])
AC_MSG_NOTICE([ Libraries:])
AC_MSG_NOTICE([])
AC_MSG_NOTICE([       GLIB2: $GLIB2_CFLAGS $GLIB2_LIBS])
AC_MSG_NOTICE([])
AC_MSG_NOTICE([         GTK: $GTK_CFLAGS $GTK_LIBS])
AC_MSG_NOTICE([])
AC_MSG_NOTICE([     GTK_VNC: $GTK_VNC_CFLAGS $GTK_VNC_LIBS])
AC_MSG_NOTICE([])
AC_MSG_NOTICE([   SPICE_GTK: $SPICE_GTK_CFLAGS $SPICE_GTK_LIBS])
AC_MSG_NOTICE([])
AC_MSG_NOTICE([     LIBXML2: $LIBXML2_CFLAGS $LIBXML2_LIBS])
AC_MSG_NOTICE([])
AC_MSG_NOTICE([     LIBVIRT: $LIBVIRT_CFLAGS $LIBVIRT_LIBS])
AC_MSG_NOTICE([])
AC_MSG_NOTICE([       OVIRT: $OVIRT_CFLAGS $OVIRT_LIBS])
AC_MSG_NOTICE([])
