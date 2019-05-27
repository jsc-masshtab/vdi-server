#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import gi
import socket
import multiprocessing
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

import logging
LOG = logging.getLogger()

from vdi_thin.layouts.splash import Image, Spinner
from vdi_thin.commands.login import LoginCommand
from vdi_thin.services.api_session import ApiSession


def ip_entry_filter(entry, *args):

    def valid(letter):
        login_window_entity = entry.get_parent().get_parent().get_parent()
        if letter in '0123456789.':
            login_window_entity.set_msg()
            return True
        else:
            login_window_entity.set_msg(_('Only numbers and dots are allowed'))
            return False

    ip = entry.get_text().strip()
    entry.handler_block_by_func(ip_entry_filter)
    entry.set_text(''.join([i for i in ip if valid(i)]))
    entry.handler_unblock_by_func(ip_entry_filter)


def port_entry_filter(entry, *args):

    def valid(letter):
        login_window_entity = entry.get_parent().get_parent().get_parent()
        if letter in '0123456789':
            login_window_entity.set_msg()
            return True
        else:
            login_window_entity.set_msg(_('Only numbers are allowed'))
            return False

    ip = entry.get_text().strip()
    entry.handler_block_by_func(port_entry_filter)
    entry.set_text(''.join([i for i in ip if valid(i)]))
    entry.handler_unblock_by_func(port_entry_filter)


def username_entry_filter(entry, *args):

    def valid(letter):
        login_window_entity = entry.get_parent().get_parent()
        if re.match("^[a-zA-Z0-9_.@-]+$", letter):
            login_window_entity.set_msg()
            return True
        else:
            login_window_entity.set_msg(_("Only latin letters, numbers, '_', '.', '@', and '-' are allowed"))
            return False

    username = entry.get_text().strip()
    entry.handler_block_by_func(username_entry_filter)
    entry.set_text(''.join([i for i in username if valid(i)]))
    entry.handler_unblock_by_func(username_entry_filter)


class Login(Gtk.ApplicationWindow):
    def __init__(self, app):
        super(Login, self).__init__()
        LOG.debug("init_login")
        self.app = app
        self.set_application(app)
        self.set_can_focus(False)
        self.set_title(app.NAME)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_destroy_with_parent(True)
        self.set_icon(app.LOGO)
        self.set_type_hint(Gdk.WindowTypeHint(1))
        self.connect("key-press-event", self.on_key_press_event)
        self.connect("delete_event", self.on_login_dialog_destroy)
        self.connect("show", self.on_login_dialog_show)

        self.wait_spinner = Spinner()
        self.msg_buffer = Gtk.TextBuffer()
        self.msg_field = Msg(self.msg_buffer)
        self.msg_field.set_wrap_mode(Gtk.WrapMode.WORD)

        form_data = self.app.load_form().get(self.app.mode, {})

        self.vbox = Gtk.VBox()

        hbox = Gtk.HBox(False, 0)
        self.ip_field = Entry(placeholder=_("hostname"),
                              tooltip=_("Hostname"),
                              action=self.on_ip_field_changed,
                              text=form_data.get('ip'),
                              margin={'top': 5, 'bottom': 5, 'left': 10})
        # self.ip_field.connect('changed', ip_entry_filter)
        # self.port_field = Spin(value=form_data.get('port'),
        #                        tooltip="Port",
        #                        action=self.on_port_field_changed)
        self.port_field = Entry(placeholder=_("port"),
                                tooltip=_("Port"),
                                action=self.on_port_field_changed,
                                text=form_data.get('port'),
                                len=5,
                                margin={'top': 5, 'bottom': 5, 'right': 10, 'left': 5})
        self.port_field.connect('changed', port_entry_filter)
        hbox.pack_start(self.ip_field, True, True, 0)
        hbox.pack_start(self.port_field, False, False, 0)

        self.username_field = Entry(placeholder=_("username"),
                                    tooltip=_("User name"),
                                    action=self.on_username_field_changed,
                                    text=form_data.get('username'),
                                    margin={'top': 5, 'bottom': 5, 'right': 10, 'left': 10})
        self.username_field.connect('changed', username_entry_filter)
        self.password_field = Entry(placeholder=_("password"),
                                    tooltip=_("Password"),
                                    action=self.on_password_field_changed,
                                    text=form_data.get('password'),
                                    visibility=False,
                                    margin={'top': 5, 'bottom': 5, 'right': 10, 'left': 10})
        #self.login_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_CONNECT))
        self.login_button = Gtk.Button()
        self.login_button.set_always_show_image(True)
        self.login_button.set_label(_("Login"))
        self.login_button.set_margin_bottom(10)
        self.login_button.connect("clicked", self.on_login_button_clicked)

        buttonbox1 = Gtk.ButtonBox()
        buttonbox1.pack_start(self.login_button, False, False, 0)

        logo = Image(self.app.LOGO)

        self.remember_user = Gtk.CheckButton(_("- remember"))
        self.remember_user.set_margin_left(20)

        self.vbox.pack_end(buttonbox1, True, True, 0)
        self.vbox.pack_end(self.wait_spinner, False, False, 0)
        self.vbox.pack_end(self.msg_field, True, True, 0)
        self.vbox.pack_end(self.remember_user, False, False, 0)
        self.vbox.pack_end(self.password_field, True, True, 0)
        if self.app.mode == 'default_mode':
            self.vbox.pack_end(self.username_field, True, True, 0)
        self.vbox.pack_end(hbox, False, False, 0)
        self.vbox.pack_end(logo, False, False, 0)

        self.add(self.vbox)
        self.show_all()
        self.msg_field.set_visible(False)

    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            if self.check_all_fields_filled():
                self.submit_data()

    def on_login_dialog_show(self, *args):
        LOG.debug("login show")
        self.normal_state()

    def on_login_dialog_destroy(self, *args):
        LOG.debug("login destroy")
        self.app.do_quit()

    def on_login_button_clicked(self, event):
        self.submit_data()

    def on_username_field_changed(self, event):
        LOG.debug("username field changed")
        self.handle_login_button_state()

    def on_password_field_changed(self, event):
        LOG.debug("password field changed")
        self.handle_login_button_state()

    def on_port_field_changed(self, event):
        LOG.debug("port field field changed")
        self.handle_login_button_state()

    def on_ip_field_changed(self, event):
        LOG.debug("ip field field changed")
        self.handle_login_button_state()

    def submit_data(self):
        if not self.app.hostname_valid(unicode(self.ip_field.get_text()), self.set_msg):
            # self.set_msg("Invalid hostname")
            return
        username = self.username_field.get_text()
        password = self.password_field.get_text()
        ip = self.ip_field.get_text()
        # port = self.port_field.get_value_as_int()
        port = self.port_field.get_text()
        if not self.check_host(ip, int(port)):
            self.set_msg(_("Hostname is not accessible"))
            return
        if self.remember_user.get_active():
            self.app.save_form(ip, port, username, password)
        else:
            self.app.save_form(ip, port, username)
        if self.app.mode == 'default_mode':
            server = "http://{ip}:{port}".format(ip=ip, port=port)
            # cmd = LoginCommand(self.app, api_session=ApiSession(username, password, server), login_handler=self)
            cmd = LoginCommand(self.app, api_session=ApiSession(username, password, ip, port), login_handler=self)
            self.wait_state(cmd(retry_count=2))
        elif self.app.mode == 'manual_mode':
            self.app.do_viewer(host=ip, port=port, password=password)
        else:
            print 'wat!? ^_^'

    # @staticmethod
    def ping(self, ip, port, send_end):
        alive = False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            ret = s.connect_ex((ip, port))
            alive = (ret != 113)
        except Exception, e:
            print e
        finally:
            s.close()
        send_end.send(alive)

    def check_host(self, ip, port):
        recv_end, send_end = multiprocessing.Pipe(False)
        p = multiprocessing.Process(target=self.ping, args=(ip, port, send_end))
        p.start()
        p.join(2)
        if p.is_alive():
            p.terminate()
            p.join()
            return False
        return recv_end.recv()

    def set_msg(self, msg=None):
        if msg:
            self.msg_buffer.set_text("")
            self.msg_field.set_visible(True)
            msg = '<span color="red">%s</span>\n' % (msg)
            self.msg_buffer.insert_markup(self.msg_buffer.get_end_iter(), msg, -1)
            # self.msg_buffer.set_text(msg)
        else:
            self.msg_field.set_visible(False)
            self.msg_buffer.set_text("")

    def normal_state(self):
        self.wait_spinner.stop()
        self.username_field.set_sensitive(True)
        self.ip_field.set_sensitive(True)
        self.port_field.set_sensitive(True)
        self.password_field.set_sensitive(True)
        self.handle_login_button_state()

    def wait_state(self, promise):
        self.login_button.set_sensitive(False)
        self.username_field.set_sensitive(False)
        self.ip_field.set_sensitive(False)
        self.port_field.set_sensitive(False)
        self.password_field.set_sensitive(False)
        self.wait_spinner.start()

    def handle_login_button_state(self):
        if self.check_all_fields_filled():
            self.login_button.set_sensitive(True)
        else:
            self.login_button.set_sensitive(False)

    def check_all_fields_filled(self):
        if self.app.mode == 'default_mode':
            return (self.username_field.get_text() and
                    self.password_field.get_text() and
                    self.ip_field.get_text() and
                    # self.port_field.get_value)
                    self.port_field.get_text())
        else:
            return (self.password_field.get_text() and
                    self.ip_field.get_text() and
                    # self.port_field.get_value)
                    self.port_field.get_text())


class Entry(Gtk.Entry):
    def __init__(self, placeholder, tooltip, action, text=None, visibility=True, len=None, margin={}):
        super(Entry, self).__init__()
        self.set_placeholder_text(placeholder)
        self.set_has_tooltip(True)
        self.set_tooltip_text(tooltip)
        if margin:
            if margin.get('left'):
                self.set_margin_left(margin['left'])
            if margin.get('right'):
                self.set_margin_right(margin['right'])
            if margin.get('top'):
                self.set_margin_top(margin['top'])
            if margin.get('bottom'):
                self.set_margin_bottom(margin['bottom'])
        # self.set_margin_right(5)
        # self.set_margin_top(5)
        # self.set_margin_bottom(5)
        self.set_visibility(visibility)
        if len:
            self.set_max_length(len)
            self.set_width_chars(len)
        if text:
            self.set_text(text)
        self.connect("changed", action)
        self.connect("activate", action)



class Spin(Gtk.SpinButton):
    def __init__(self, value, tooltip, action):
        super(Spin, self).__init__()
        self.set_margin_right(20)
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.set_tooltip_text(tooltip)
        self.set_numeric(True)
        self.set_max_length(5)
        self.set_update_policy(Gtk.SpinButtonUpdatePolicy.ALWAYS)
        self.set_digits(0)
        # Gtk.Adjustment (
        #     value, // Начальное значение
        #     lower, // Минимальное значение
        #     upper, // Максимальное значение
        #     step_increment, // Шаг приращения
        #     page_increment, // Страничное приращение
        #     page_size); // Размер страницы
        # )
        self.set_adjustment(Gtk.Adjustment(1, 1, 99999, 1, 0, 0))
        if value:
            self.set_value(value)
        self.connect("change-value", self.update)
        self.connect("value-changed", action)
        self.connect("activate", action)

class Msg(Gtk.TextView):
    def __init__(self, buffer):
        super(Msg, self).__init__()
        self.set_can_focus(True)
        self.set_margin_left(20)
        self.set_margin_right(20)
        self.set_margin_top(5)
        self.set_editable(False)
        self.set_buffer(buffer)

