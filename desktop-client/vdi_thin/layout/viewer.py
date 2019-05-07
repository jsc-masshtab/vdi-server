# -*- coding: utf-8 -*-

from os import path
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('SpiceClientGtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, SpiceClientGtk, SpiceClientGLib, GObject, Gdk, GLib, WebKit2, GdkPixbuf

import logging
LOG = logging.getLogger()

VERSION = "1.0"
AUTHORS = [u'АО "НИИ "МАСШТАБ"']
COMMENTS = ""
WEBSITE = "http://mashtab.org/"


def build_keycombo_menu(on_send_key_fn):
    menu = Gtk.Menu()

    def make_item(name, combo):
        item = Gtk.MenuItem.new_with_mnemonic(name)
        item.connect("activate", on_send_key_fn, combo)
        menu.add(item)

    make_item("Ctrl+Alt+_Backspace", ["Control_L", "Alt_L", "BackSpace"])
    make_item("Ctrl+Alt+_Delete", ["Control_L", "Alt_L", "Delete"])
    menu.add(Gtk.SeparatorMenuItem())

    for i in range(1, 13):
        make_item("Ctrl+Alt+F_%d" % i, ["Control_L", "Alt_L", "F%d" % i])
    menu.add(Gtk.SeparatorMenuItem())

    make_item("_Printscreen", ["Print"])

    menu.show_all()
    return menu


def build_reset_menu(on_vm_manage_fn, default_mode=False):
    menu = Gtk.Menu()

    def make_item(name, combo=None):
        item = Gtk.MenuItem.new_with_mnemonic(name)
        item.item_name = name
        item.connect("activate", on_vm_manage_fn, combo)
        menu.add(item)

    make_item("Disconnect")
    # make_item("+Monitor")
    if default_mode:
        menu.add(Gtk.SeparatorMenuItem())
        make_item("Run")
        make_item("Pause")
        menu.add(Gtk.SeparatorMenuItem())
        make_item("Reboot")
        make_item("Power off")
        menu.add(Gtk.SeparatorMenuItem())
        make_item("Reset")
        make_item("Force power off")

    menu.show_all()
    return menu


class Viewer(Gtk.ApplicationWindow):
    title = 'ECP Veil VDI Client'

    def __init__(self, app, vm_widget, **kwargs):
        super(Viewer, self).__init__()
        LOG.debug("init_viewer")
        self.app = app
        self.set_application(app)
        self.set_can_focus(False)
        self.set_icon(self.app.LOGO)
        self.set_default_geometry(1280, 720)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.kwargs = kwargs

        self.connect("key-press-event", self.on_key_press_event)
        self.connect("delete-event", self.on_viewer_delete_event)
        self.connect("show", self.on_viewer_show)

        self.vm_widget = vm_widget

        self.session = None
        self.display = None
        self.display_channel = None
        self.frame = Gtk.Frame()
        self.frame.set_shadow_type(Gtk.ShadowType.NONE)
        self._usbdev_manager = None
        self.fs = False

        self._overlay_toolbar_fullscreen = OverlayToolbar(self.app)
        self._overlay = self._overlay_toolbar_fullscreen.create(
            name="Fullscreen Toolbar",
            tooltip_text="Leave fullscreen",
            accessible_name="Fullscreen Exit",
            send_key_accessible_name="Fullscreen Send Key",
            on_leave_fn=self.toggle_fullscreen,
            on_send_key_fn=self._do_send_key,
            on_vm_manage_fn=self._vm_control,
            on_usb_fn=self.control_vm_usb_redirection,
            usb_tooltip="Redirection USB devices",
            on_close_fn=self.on_viewer_delete_event,
            close_tooltip="Close")
        self.overlay = Gtk.Overlay()
        self.overlay.add_overlay(self._overlay)

        self.mb = Gtk.MenuBar()

        viewmenu = Gtk.Menu()
        viewm = Gtk.MenuItem("View")
        viewm.set_submenu(viewmenu)
        self.mb.append(viewm)
        self.screen_mode_toggle = self.add_menu_item(viewmenu,
                                                     self.toggle_fullscreen,
                                                     "Fullscreen")
        self.add_menu_item(viewmenu, self.resize_to_vm, "Resize to VM")

        usbmenu = Gtk.Menu()
        usbm = Gtk.MenuItem("Usb")
        usbm.set_submenu(usbmenu)
        self.mb.append(usbm)
        self.add_menu_item(usbmenu, self.control_vm_usb_redirection, "Redirection USB devices")

        keys_menu = build_keycombo_menu(self._do_send_key)
        keycombom = Gtk.MenuItem("Send keys")
        keycombom.set_submenu(keys_menu)
        self.mb.append(keycombom)

        if self.app.mode != 'fast_mode':
            vm_menu = build_reset_menu(self._vm_control, bool(self.app.mode == 'default_mode'))
            vmm = Gtk.MenuItem("Control")
            vmm.set_submenu(vm_menu)
            self.mb.append(vmm)

        helpmenu = Gtk.Menu()
        helpm = Gtk.MenuItem("Help")
        helpm.set_submenu(helpmenu)
        self.mb.append(helpm)
        self.add_menu_item(helpmenu, self.show_help, "Help")
        self.add_menu_item(helpmenu, self.about, "About")

        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(self.mb, False, False, 0)

        vbox.pack_end(self.frame, True, True, 0)
        self.overlay.add(vbox)
        self.add(self.overlay)

    def on_viewer_delete_event(self, *args):
        LOG.debug("quit viewer")
        if self.app.confirm_quit():
            if self.session is not None:
                self.session.disconnect()
            self.session = None
            self.audio = None
            if self.display:
                self.display.destroy()
            self.display = None
            self.display_channel = None
            self.app.do_quit()
        else:
            return True

    def disconnect(self, *args):
        if self.app.confirm_logout():
            if self.app.mode == 'default_mode':
                self.app.do_main()
            else:
                self.app.do_logout()

    def on_viewer_show(self, *args):
        LOG.debug("viewer show")
        self.main_loop()

    def show_help(self, *args):
        mydir = path.abspath(path.dirname(__file__))
        ctx = WebKit2.WebContext.get_default()
        ctx.set_web_extensions_directory(mydir)
        ctx.set_web_extensions_initialization_user_data(GLib.Variant.new_string("test string"))

        help_window = Gtk.Window()
        help_window.set_title("Official ECP Veil page")
        webview = WebKit2.WebView.new_with_context(ctx)
        help_window.add(webview)
        help_window.set_transient_for(self)
        help_window.set_icon(self.app.LOGO)
        help_window.set_default_size(640, 480)
        help_window.show_all()

        webview.load_uri("http://mashtab.org/files/veil/index.html")

    def _vm_control(self, *args):
        if args[0].item_name == 'Disconnect':
            self.disconnect()
        # - Testing code -
        # elif args[0].item_name == '+Monitor':
        #
        #     new_display = Gtk.ApplicationWindow()
        #     new_display.set_application(self.app)
        #     new_display.frame = Gtk.Frame()
        #     box = Gtk.VBox(False, 2)
        #     box.pack_end(new_display.frame, True, True, 0)
        #     new_display.add(box)
        #     new_display.display = SpiceClientGtk.Display.new_with_monitor(self.session,
        #                                                                   self.display.get_property("channel_id"),
        #                                                                   1)
        #     new_display.frame.add(new_display.display)
        #     new_display.display.realize()
        #     new_display.display.show_all()
        #
        #     new_display.show_all()
        #
        #     self.app.window = new_display
        #     self.app.window.present()
        else:
            print('Not implemented on server side yet')

    def _do_send_key(self, src, keys):
        ignore = src
        if keys is not None:
            self._send_keys(keys)

    def on_key_press_event(self, widget, event):
        # print("Key press on widget: ", widget)
        # print("          Modifiers: ", event.state)
        # print("      Key val, name: ", event.keyval, Gdk.keyval_name(event.keyval))
        ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
        alt = (event.state & Gdk.ModifierType.MOD1_MASK)
        if ctrl and alt:
            if event.keyval == Gdk.KEY_f:
                self.toggle_fullscreen()
            elif event.keyval == Gdk.KEY_r:
                self.resize_to_vm()

    def about(self, *args):
        about = Gtk.AboutDialog()
        about.set_transient_for(self)
        about.set_program_name(self.app.NAME_THIN)
        about.set_version(VERSION)
        about.set_authors(AUTHORS)
        about.set_comments(COMMENTS)
        about.set_website(WEBSITE)
        about.set_logo(self.app.LOGO)
        about.run()
        about.destroy()

    def resize_to_vm(self, *args):
        width, height = self.display_channel.get_properties("width", "height")
        self.resize(width, height)

    def toggle_fullscreen(self, *args):
        if self.fs:
            self.mb.show()
            self.unfullscreen()
            self.fs = False
            self.screen_mode_toggle.set_label("Fullscreen")
            self._overlay_toolbar_fullscreen.timed_revealer.force_reveal(False)
        else:
            self.mb.hide()
            self.fullscreen()
            self.fs = True
            self.screen_mode_toggle.set_label("Windowed mode")
            self._overlay_toolbar_fullscreen.timed_revealer.force_reveal(True)

    def add_menu_item(self, menu, command, title):
        item = Gtk.MenuItem()
        item.set_label(title)
        item.connect("activate", command)
        menu.append(item)
        menu.show_all()
        return item

    def add_seperator(self, menu):
        item = Gtk.SeparatorMenuItem()
        menu.append(item)
        menu.show_all()

    def _send_keys(self, keys):
        return self.display.send_keys([Gdk.keyval_from_name(k) for k in keys],
                                      SpiceClientGtk.DisplayKeyEvent.CLICK)

    def settings(self, host, port):
        self.session = SpiceClientGLib.Session()
        SpiceClientGLib.set_session_option(self.session)
        uri = "spice://"
        uri += str(host) + "?port=" + str(port)
        self.session.set_property("uri", uri)

        gtk_session = SpiceClientGtk.GtkSession.get(self.session)
        gtk_session.set_property("auto-clipboard", True)

        GObject.GObject.connect(self.session, "channel-new", self._channel_new)

        try:
            self._usbdev_manager = SpiceClientGLib.UsbDeviceManager.get(self.session)
            self._usbdev_manager.connect("auto-connect-failed", self._usbdev_redirect_error)
            self._usbdev_manager.connect("device-error", self._usbdev_redirect_error)
            gtk_session.set_property("auto-usbredir", True)
        except Exception:
            self._usbdev_manager = None
            logging.debug("Error initializing spice usb device manager", exc_info=True)

    def _channel_new(self, session, channel):
        self._channel = channel
        if type(channel) == SpiceClientGLib.MainChannel:
            return
        if type(channel) == SpiceClientGLib.DisplayChannel:
            channel_id = channel.get_property("channel-id")
            self.display_channel = channel
            self.display = SpiceClientGtk.Display.new(self.session, channel_id)
            # self.display = SpiceClientGtk.Display.new_with_monitor(self.session, channel_id, self.monitor_id)
            self.frame.add(self.display)
            self.display.realize()
            self.display.set_property("resize-guest", True)
            self.display.set_property("scaling", False)
            # cant read monitor cfg
            # print SpiceClientGLib.DisplayMonitorConfig().id
            # print SpiceClientGLib.DisplayChannel.props.monitors
            # arr = channel.get_property('monitors')
            self.display.show_all()
            return

    def control_vm_usb_redirection(self, action):
        ignore = action
        spice_usbdev_widget = self._get_usb_widget()
        spice_usbdev_widget.set_margin_left(10)
        spice_usbdev_widget.set_margin_right(10)
        if not spice_usbdev_widget:
            return
        spice_usbdev_dialog = Gtk.MessageDialog(self,
                                                title="Redirection USB devices",
                                                flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                                # message_type=Gtk.MessageType.INFO,
                                                buttons=Gtk.ButtonsType.CLOSE)
        spice_usbdev_dialog.get_content_area().add(spice_usbdev_widget)
        spice_usbdev_dialog.show_all()
        spice_usbdev_dialog.run()
        spice_usbdev_dialog.destroy()

    def _get_usb_widget(self, *args):
        if not self.session:
            return
        usbwidget = SpiceClientGtk.UsbDeviceWidget.new(self.session, '%s, %s')
        usbwidget.connect("connect-failed", self._usbdev_redirect_error)
        return usbwidget

    def _usbdev_redirect_error(self, spice_usbdev_widget, spice_usb_device, errstr):
        ignore = spice_usbdev_widget
        ignore = spice_usb_device
        LOG.debug("Usb redirection error")
        raise NotImplementedError("Usb redirection error")

    def main_loop(self):
        if self.vm_widget:
            self.set_title(self.title + self.vm_widget.vm_data['name'])
        else:
            self.set_title('{title} - {host}:{port}'.format(title=self.title,
                                                            host=self.kwargs['host'],
                                                            port=self.kwargs['port']))
        self.settings(self.kwargs['host'], self.kwargs['port'])
        if self.kwargs['password']:
            self.session.set_property("password", self.kwargs['password'])
            self.session.connect()
            self.show_all()
            # self.toggle_fullscreen()

    def _has_agent(self):
        if not self._channel:
            return False
        return self._channel.get_property("agent-connected")


class _TimedRevealer(GObject.GObject):
    """
    Revealer for the fullscreen toolbar, with a bit of extra logic to
    hide/show based on mouse over
    """
    def __init__(self, toolbar):
        GObject.GObject.__init__(self)

        self._in_fullscreen = False
        self._timeout_id = None
        self._gobject_timeouts = []

        self._revealer = Gtk.Revealer()
        self._revealer.add(toolbar)

        # Adding the revealer to the eventbox seems to ensure the
        # eventbox always has 1 invisible pixel showing at the top of the
        # screen, which we can use to grab the pointer event to show
        # the hidden toolbar.

        self._ebox = Gtk.EventBox()
        self._ebox.add(self._revealer)
        self._ebox.set_halign(Gtk.Align.CENTER)
        self._ebox.set_valign(Gtk.Align.START)
        self._ebox.show_all()

        self._ebox.connect("enter-notify-event", self._enter_notify)
        self._ebox.connect("leave-notify-event", self._enter_notify)

    def _cleanup(self):
        self._ebox.destroy()
        self._ebox = None
        self._revealer.destroy()
        self._revealer = None
        self._timeout_id = None

    def _enter_notify(self, ignore1, ignore2):
        x, y = self._ebox.get_pointer()
        alloc = self._ebox.get_allocation()
        entered = bool(x >= 0 and y >= 0 and x < alloc.width and y < alloc.height)

        if not self._in_fullscreen:
            return

        # Pointer exited the toolbar, and toolbar is revealed. Schedule
        # a timeout to close it, if one isn't already scheduled
        if not entered and self._revealer.get_reveal_child():
            self._schedule_unreveal_timeout(1000)
            return

        self._unregister_timeout()
        if entered and not self._revealer.get_reveal_child():
            self._revealer.set_reveal_child(True)

    def _schedule_unreveal_timeout(self, timeout):
        if self._timeout_id:
            return

        def cb():
            self._revealer.set_reveal_child(False)
            self._timeout_id = None
        self._timeout_id = self.timeout_add(timeout, cb)

    def _unregister_timeout(self):
        if self._timeout_id:
            self.remove_gobject_timeout(self._timeout_id)
            self._timeout_id = None

    def force_reveal(self, val):
        self._unregister_timeout()
        self._in_fullscreen = val
        self._revealer.set_reveal_child(val)
        self._schedule_unreveal_timeout(2000)

    def get_overlay_widget(self):
        return self._ebox

    def timeout_add(self, timeout, func, *args):
        """
        GLib timeout_add wrapper to simplify callers, and track handles
        for easy cleanup
        """
        ret = GLib.timeout_add(timeout, func, *args)
        self.add_gobject_timeout(ret)
        return ret

    def add_gobject_timeout(self, handle):
        self._gobject_timeouts.append(handle)

    def remove_gobject_timeout(self, handle):
        GLib.source_remove(handle)
        self._gobject_timeouts.remove(handle)


class OverlayToolbar:
    def __init__(self, app):
        self.app = app
        self.send_key_button = None
        self.vm_button = None
        self.timed_revealer = None
        self.keycombo_menu = None
        self.vm_menu = None
        self.toolbar = None
        self.timed_revealer = None
        self.overlay_toolbar = None

    def create(self, name, tooltip_text, accessible_name,
               send_key_accessible_name, on_leave_fn,
               on_send_key_fn, on_vm_manage_fn,
               on_usb_fn, usb_tooltip,
               on_close_fn, close_tooltip):
        self.keycombo_menu = build_keycombo_menu(on_send_key_fn)
        self.keycombo_menu.loc = 2
        self.vm_menu = build_reset_menu(on_vm_manage_fn, bool(self.app.mode == 'default_mode'))
        self.vm_menu.loc = 3

        self.overlay_toolbar = Gtk.Toolbar()
        self.overlay_toolbar.set_icon_size(Gtk.IconSize.DIALOG)
        self.overlay_toolbar.set_show_arrow(False)
        self.overlay_toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        self.overlay_toolbar.get_accessible().set_name(name)

        button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_LEAVE_FULLSCREEN)
        button.set_tooltip_text(tooltip_text)
        button.show()
        button.get_accessible().set_name(accessible_name)
        self.overlay_toolbar.add(button)
        button.connect("clicked", on_leave_fn)

        usb_button = Gtk.ToolButton()
        usb_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    filename="content/img/usb.png",
                    width=48,
                    height=48,
                    preserve_aspect_ratio=True)
        usb_icon = Gtk.Image.new_from_pixbuf(usb_pixbuf)
        usb_button.set_icon_widget(usb_icon)
        # usb_button.set_icon_name("media-flash")
        usb_button.set_tooltip_text(usb_tooltip)
        usb_button.show()
        self.overlay_toolbar.add(usb_button)
        usb_button.connect("clicked", on_usb_fn)

        # Exit button

        def keycombo_menu_clicked(src, menu):
            ignore = src
            def menu_location(*args):
                # Signature changed at some point.
                #  f23+    : args = menu, x, y, toolbar
                #  rhel7.3 : args = menu, toolbar
                button_quantity = 5
                if self.app.mode == 'fast_mode':
                    button_quantity -= 1
                _menu = args[0]
                if len(args) == 4:
                    _toolbar = args[3]
                else:
                    _toolbar = args[1]

                ignore, x, y = _toolbar.get_window().get_origin()
                height = _toolbar.get_window().get_height()
                width = _toolbar.get_window().get_width()
                shift = (width/button_quantity)/2 + width/button_quantity * _menu.loc
                return x + shift, y + height, True

            menu.popup(None, None, menu_location,
                       self.overlay_toolbar, 0,
                       Gtk.get_current_event_time())

        self.send_key_button = Gtk.ToolButton()
        self.send_key_button.set_icon_name(
            "preferences-desktop-keyboard-shortcuts")
        self.send_key_button.set_tooltip_text("Send key combination")
        self.send_key_button.show_all()
        self.send_key_button.connect("clicked", lambda *args: keycombo_menu_clicked(args, self.keycombo_menu))
        self.send_key_button.get_accessible().set_name(
            send_key_accessible_name)
        self.overlay_toolbar.add(self.send_key_button)

        if self.app.mode != 'fast_mode':
            self.vm_button = Gtk.ToolButton()
            control_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                filename="content/img/control.png",
                width=48,
                height=48,
                preserve_aspect_ratio=True)
            control_icon = Gtk.Image.new_from_pixbuf(control_pixbuf)
            self.vm_button.set_icon_widget(control_icon)
            # self.vm_button.set_icon_name("preferences-desktop")
            self.vm_button.set_tooltip_text("Control")
            self.vm_button.show_all()
            self.vm_button.connect("clicked", lambda *args: keycombo_menu_clicked(args, self.vm_menu))
            self.overlay_toolbar.add(self.vm_button)

        close_button = Gtk.ToolButton.new_from_stock(Gtk.STOCK_CLOSE)
        close_button.set_tooltip_text(close_tooltip)
        close_button.show()
        self.overlay_toolbar.add(close_button)
        close_button.connect("clicked", on_close_fn)

        self.timed_revealer = _TimedRevealer(self.overlay_toolbar)
        return self.timed_revealer.get_overlay_widget()

    def cleanup(self):
        self.keycombo_menu.destroy()
        self.keycombo_menu = None
        self.overlay_toolbar.destroy()
        self.overlay_toolbar = None
        self.timed_revealer.cleanup()
        self.timed_revealer = None

    def set_sensitive(self, can_sendkey):
        self.send_key_button.set_sensitive(can_sendkey)

