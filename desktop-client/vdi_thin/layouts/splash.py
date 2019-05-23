import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import logging
LOG = logging.getLogger()


class Splash(Gtk.ApplicationWindow):
    def __init__(self, app):
        super(Splash, self).__init__()
        LOG.debug("init_splash")
        self.set_can_focus(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon(app.LOGO)
        self.set_decorated(False)
        self.set_show_menubar(False)
        self.set_application(app)

        vbox = Gtk.VBox()
        vbox.pack_start(Image(app.LOGO), False, True, 0)
        vbox.pack_start(Label(app.NAME), False, True, 1)
        vbox.pack_start(Spinner(), False, True, 2)

        self.add(vbox)
        self.show_all()


class Image(Gtk.Image):
    def __init__(self, logo):
        super(Image, self).__init__()
        self.set_visible(True)
        self.set_can_focus(False)
        self.set_margin_left(10)
        self.set_margin_right(10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_from_pixbuf(logo)


class Label(Gtk.Label):
    def __init__(self, title):
        super(Label, self).__init__()
        self.set_visible(True)
        self.set_can_focus(False)
        self.set_hexpand(True)
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.set_label(title)


class Spinner(Gtk.Spinner):
    def __init__(self):
        super(Spinner, self).__init__()
        self.set_visible(True)
        self.set_can_focus(False)
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.start()

