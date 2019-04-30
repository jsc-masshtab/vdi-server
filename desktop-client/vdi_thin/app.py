# -*- coding: utf-8 -*-


import os
import logging
import json


import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk, GdkPixbuf

LOG = logging.getLogger()

from .layout.splash import Splash
from .layout.login import Login
from .layout.main import Main
from .layout.viewer import Viewer
from .commands.splashcommand import SplashCommand


def help(msg='Help page'):
    print '''
{}
            
ECP Veil VDI client has tree modes:

    1) Default mode. NO keys. Starts VDI server login dialog.

    2) Manual mode. Only one key "-m". Start GUI dialog for enter ip, port and
       password for connect VM. VDI server is not needed.
        -m  - manual mode

    3) Fast mode for open VM viewer right away. VDI server is not needed.
        -ip <ip-address>
        -p  <port>
        -pw <password>
        '''.format(msg)


class AppState:
    def __init__(self, app):
        self.app = app

    @property
    def logged_in(self):
        return self.app.api_session is not None


class Application(Gtk.Application):

    LOGO = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath("content/img/veil-32x32.png"))
    NAME = "ECP Veil VDI"
    NAME_THIN = "ECP Veil VDI thin client"
    NAME_MANAGER = "ECP Veil VDI manager"

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args,
                                          application_id="org.mashtab.vdi_client",
                                          flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                                          **kwargs)

        self.first_login = True
        self.window = None

        self.splash_window = None

        self.state = AppState(self)
        self.api_session = None

        self.workers_promises = {}

    def run(self, args):
        self._args = args
        self._args.pop(0)
        Gtk.Application.run(self)

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

        def get_value(k):
            try:
                val = self._args[self._args.index(k)+1]
            except IndexError:
                return False
            if val[0] != '-':
                return val
            else:
                return False

        if len(self._args) == 0:
            self.mode = 'default_mode'
            if self.api_session:
                self.do_main()
            else:
                self.do_login()
        elif len(self._args) == 1:
            if '-m' in self._args:
                self.mode = 'manual_mode'
                self.do_login()
            elif '-h' in self._args or '-help' in self._args:
                help()
            else:
                help('Error:\n    Wrong key for Manual mode: {}'.format(self._args[0]))
        else:
            allowed_keys = ['-ip', '-p', '-pw']
            values = dict()
            for key in self._args:
                if key in allowed_keys:
                    value = get_value(key)
                    if value:
                        values[key] = value
            missed_keys = list(set(allowed_keys) - set(values.keys()))
            if not missed_keys:
                self.mode = 'fast_mode'
                self.do_viewer(host=values['-ip'], port=values['-p'], password=values['-pw'])
            else:
                help('Error:\n    Missed key(s) or its value(s): {}'.format(', '.join(missed_keys)))

    def destroy_active_window(self):
        if self.window:
            self.window.destroy()
            self.window = None

    def do_viewer(self, *args, **kwargs):
        LOG.debug('viewer')
        self.destroy_active_window()
        self.window = Viewer(self, False, **kwargs)
        self.window.present()

    def do_main(self):
        LOG.debug('main')
        self.destroy_active_window()
        self.window = Main(self)
        self.window.present()

    def _login(self, *args):
        LOG.debug('login')
        self.destroy_active_window()
        self.window = Login(self)
        self.window.present()

    def do_login(self):
        if self.first_login:
            LOG.debug('splash')
            self.first_login = False
            self.window = Splash(self)
            self.window.present()
            cmd = SplashCommand(self, on_finish=self._login)
            cmd()
        else:
            self._login()

    def save_form(self, ip, port, username, password=''):
        f_data = self.load_form()
        f_data[self.mode] = dict(ip=ip, port=port, username=username, password=password)
        with open('user_input.json', 'w') as f:
            json.dump(f_data, f)

    def load_form(self):
        try:
            with open('user_input.json', 'r') as f:
                return json.load(f)
        except IOError, ioe:
            print str(ioe)
            logging.debug(str(ioe))
            return {}
        except Exception, e:
            with open('user_input.json', 'w') as f:
                json.dump({self.mode: {}}, f)
            logging.debug("user_input file created")
            return {}

    def do_command_line(self, command_line):
        LOG.debug('command_line')
        options = command_line.get_options_dict()

        if options.contains("test"):
            LOG.debug("Test argument received")

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
        form_data = self.load_form()
        if form_data:
            self.save_form(form_data[self.mode]['ip'], form_data[self.mode]['port'], form_data[self.mode]['username'])
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
        dialog.set_resizable(False)
        label = Gtk.Label.new(question)
        label.set_margin_top(20)
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
        return self.simple_confirm("Confirm action", "Quit?")

    def confirm_logout(self):
        return self.simple_confirm("Confirm action", "Logout?")
