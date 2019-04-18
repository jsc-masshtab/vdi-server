#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import logging


import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk, GdkPixbuf

LOG = logging.getLogger()

from .layout.splash import Splash
from .layout.login import Login
from .layout.main import Main
from .commands.splashcommand import SplashCommand


class AppState():
    def __init__(self, app):
        self.app = app
        self.viewer_process = {}

    @property
    def logged_in(self):
        return self.app.api_session is not None


class Application(Gtk.Application):

    LOGO = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath("content/img/veil-32x32.png"))
    NAME = "ECP Veil VDI"
    NAME_THIN = "ECP Veil VDI thin client"
    NAME_MANAGER = "ECP Veil VDI manager"

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, application_id="org.mashtab.vdi_client",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                         **kwargs)
        self.first_login = True
        self.window = None

        self.splash_window = None

        self.state = AppState(self)
        self.api_session = None

        self.workers_promises = {}

    def init_menu(self):
        pass
        # menu_builder = Gtk.Builder()
        # menu_builder.add_from_file("glade/menu.xml")
        # main_menu = menu_builder.get_object("main_menu")
        # self.set_app_menu(main_menu)

    def register_actions(self):
        quit = Gio.SimpleAction.new("quit", None)
        logout = Gio.SimpleAction.new("logout", None)
        quit.connect("activate", self.on_quit)
        logout.connect("activate", self.on_logout)
        self.add_action(quit)
        self.add_action(logout)

    def do_startup(self):
        LOG.debug('startup')
        Gtk.Application.do_startup(self)
        self.register_actions()
        self.init_menu()

    def do_activate(self):
        LOG.debug('activate')
        if self.api_session:
            self.do_main()
        else:
            self.do_login()

    def destroy_active_window(self):
        if self.window:
            self.window.destroy()
            self.window = None

    def do_main(self):
        LOG.debug('main')
        self.destroy_active_window()
        self.window = Main(self)
        self.window.present()

    def _login(self, *args):
        #self.window.hide()
        self.destroy_active_window()
        #login_dialog = Login(self, self.window)
        self.window = Login(self)
        self.window.present()
        #login_dialog.present()

    def do_login(self):
        LOG.debug('login')
        self.destroy_active_window()

        self.window = Splash(self)
        self.window.present()
        if self.first_login:
            self.first_login = False

            cmd = SplashCommand(self, on_finish=self._login)
            cmd()
        else:
            self._login()

    def do_command_line(self, command_line):
        LOG.debug('command_line')
        options = command_line.get_options_dict()

        if options.contains("test"):
            LOG.debug("Test argument recieved")

        self.activate()
        return 0

    def on_quit(self, action, param):
        if self.confirm_quit():
            self.do_quit()

    def on_logout(self, action, param):
        if self.confirm_logout():
            self.do_logout()

    def do_quit(self):
        LOG.debug('quit')
        self.force_stop_workers()
        self.quit()

    def do_logout(self):
        LOG.debug("logout")
        self.api_session = None
        self.window.hide()
        self.do_login()

    def register_worker_promise(self, promise):
        LOG.debug("register worker promise")
        self.workers_promises[promise.id] = promise

    def unregister_worker_promise(self, promise_id):
        LOG.debug("unregister worker promise")
        self.workers_promises.pop(promise_id, None)

    def force_stop_workers(self):
        LOG.debug("force stop workers")
        for promise in self.workers_promises.values():
            promise.force_stop()

    def simple_confirm(self, title, question):
        dialog = Gtk.Dialog(title, self.window, 0,
                            (Gtk.STOCK_NO, Gtk.ResponseType.NO,
                             Gtk.STOCK_YES, Gtk.ResponseType.YES
                             ))

        dialog.set_default_size(150, 100)
        label = Gtk.Label.new(question)
        label.set_margin_top(15)
        box = dialog.get_content_area()
        box.add(label)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            return True
        elif response == Gtk.ResponseType.NO:
            return False

    def confirm_quit(self):
        return self.simple_confirm("quit confirm", "Quit?")

    def confirm_logout(self):
        return self.simple_confirm("logout confirm", "Logout?")
