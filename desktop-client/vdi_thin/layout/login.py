#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

import logging
LOG = logging.getLogger()

from vdi_thin.layout.splash import Image, Spinner
from vdi_thin.commands.login import LoginCommand
from vdi_thin.services.api_session import ApiSession


#class Login(Gtk.Dialog):
class Login(Gtk.ApplicationWindow):
    def __init__(self, app):
        super(Login, self).__init__()
        LOG.debug("init_login")
        self.app = app
        self.set_application(app)
        #self.set_transient_for(parent_window)
        self.set_destroy_with_parent(True)
        self.set_can_focus(False)
        self.set_title(app.NAME)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_destroy_with_parent(True)
        self.set_icon(app.LOGO)
        self.set_type_hint(Gdk.WindowTypeHint(1))
        self.connect("destroy", self.on_login_dialog_destroy)
        self.connect("show", self.on_login_dialog_show)

        self.wait_spinner = Spinner()
        self.msg_buffer = Gtk.TextBuffer()
        self.msg_field = Msg(self.msg_buffer)

        form_data = self.load_form()

        self.vbox = Gtk.VBox()

        hbox = Gtk.HBox(False, 0)
        self.ip_field = Entry(placeholder="server IP-address",
                              tooltip="Server IP-address",
                              action=self.on_ip_field_changed,
                              text=form_data.get('ip'))
        self.port_field = Spin(value=form_data.get('port'),
                               tooltip="Port",
                               action=self.on_port_field_changed)
        hbox.pack_start(self.ip_field, True, True, 0)
        hbox.pack_start(self.port_field, False, False, 1)

        self.username_field = Entry(placeholder="username",
                                    tooltip="User name",
                                    action=self.on_username_field_changed,
                                    text=form_data.get('username'))
        self.password_field = Entry(placeholder="password",
                                    tooltip="Password",
                                    action=self.on_password_field_changed,
                                    text=form_data.get('password'),
                                    visibility=False)
        self.login_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_CONNECT))
        self.login_button.set_always_show_image(True)
        self.login_button.set_label("Login")
        self.login_button.set_margin_bottom(10)
        self.login_button.connect("clicked", self.on_login_button_clicked)

        buttonbox1 = Gtk.ButtonBox()
        buttonbox1.pack_start(self.login_button, False, False, 0)

        logo = Image(self.app.LOGO)

        self.remember_user = Gtk.CheckButton("- remember me")
        self.remember_user.set_margin_left(20)

        self.vbox.pack_end(buttonbox1, True, True, 0)
        self.vbox.pack_end(self.wait_spinner, False, False, 0)
        self.vbox.pack_end(self.msg_field, True, True, 0)
        self.vbox.pack_end(self.remember_user, False, False, 0)
        self.vbox.pack_end(self.password_field, True, True, 0)
        self.vbox.pack_end(self.username_field, True, True, 0)
        self.vbox.pack_end(hbox, False, False, 0)
        self.vbox.pack_end(logo, False, False, 0)

        self.add(self.vbox)
        self.show_all()
        self.msg_field.set_visible(False)

    def on_login_dialog_show(self, *args):
        LOG.debug("login show")
        self.normal_state()

    def on_login_dialog_destroy(self, *args):
        LOG.debug("login destroy")
        if not self.app.state.logged_in:
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
        username = self.username_field.get_text()
        password = self.password_field.get_text()
        ip = self.ip_field.get_text()
        port = self.port_field.get_value_as_int()
        if self.remember_user.get_active():
            self.save_form(ip, port, username, password)
        else:
            self.save_form(ip, port, username)
        server = "http://{ip}:{port}".format(ip=ip, port=port)
        cmd = LoginCommand(self.app, api_session=ApiSession(username, password, server),
                           login_handler=self)
        self.wait_state(cmd(retry_count=2))

    def save_form(self, ip, port, username, password=''):
        with open('user_input.json', 'w') as f:
            f.write(json.dumps(dict(ip=ip, port=port, username=username, password=password)))

    def load_form(self):
        try:
            with open('user_input.json', 'r') as f:
                return json.load(f)
        except:
            with open('user_input.json', 'w') as f:
                f.write(json.dumps({}))
            return {}

    def set_msg(self, msg=None):
        if msg:
            self.msg_buffer.set_text("")
            self.msg_field.set_visible(True)
            msg = '<span color="red">{:s}</span>\n'.format(msg)
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
        return (self.username_field.get_text() and
                self.password_field.get_text() and
                self.ip_field.get_text() and
                self.port_field.get_value)


# class Button(Gtk.Button):
#     def __init__(self, label, action, tooltip):
#         super(Button, self).__init__()
#         self.set_sensitive(False)
#         self.set_can_focus(False)
#         self.set_visible(True)
#         self.set_has_tooltip(True)
#         self.set_tooltip_text(tooltip)
#         self.set_label(label)
#         self.connect("clicked", action)
#

class Entry(Gtk.Entry):
    def __init__(self, placeholder, tooltip, action, text=None, visibility=True):
        super(Entry, self).__init__()
        self.set_placeholder_text(placeholder)
        self.set_has_tooltip(True)
        self.set_tooltip_text(tooltip)
        self.set_margin_left(20)
        self.set_margin_right(20)
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.set_visibility(visibility)
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

