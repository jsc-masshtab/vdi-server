# -*- coding: utf-8 -*-

import random
import time

import gevent

import gi
from gi.repository import GLib, GObject, SpiceClientGLib
gi.require_version("Gtk", "3.0")


# Сделано по этому примеру https://docs.locust.io/en/1.3.1/testing-other-systems.html
class SpiceSession:

    locust_environment = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._is_connected = False

        # self._main_channel = None
        self._cursor_channel = None
        self._input_channel = None

    def emulate_client(self, host, port, password, username, vm_verbose_name):

        request_type = "Spice"
        request_name = "Spice connection test"
        start_time = time.time()

        common_except_data = "VDI username: {}  Host: {}  Port: {}  Password: {} VM name: {}".\
            format(username, host, port, password, vm_verbose_name)

        try:
            if host is None or port is None:
                raise RuntimeError("No connection data.  {}.".format(common_except_data))

            # Create spice session
            spice_session = SpiceClientGLib.Session()
            SpiceClientGLib.set_session_option(spice_session)
            uri = "spice://" + str(host) + "?port=" + str(port)
            spice_session.set_property("uri", uri)
            spice_session.set_property("password", password)

            GObject.GObject.connect(spice_session, "channel-new", self._on_channel_new_created)

            # Connect
            res = spice_session.connect()
            if not res:
                raise RuntimeError("Failed to initiate connection.  {}".format(common_except_data))

            main_loop = GLib.MainLoop()
            ctx = main_loop.get_context()

            connection_timeout = 3  # sec
            conn_wait_start_time = time.time()

            # Так как использование glib loop run заблокировало бы gevent loop (используемый locust),
            # то проверяем наличие событий вручную в цикле.
            while 1:
                elapsed_time = self._get_elapsed_time(conn_wait_start_time)
                # print("elapsed_time ", elapsed_time)
                # Если соединение не установлено за время connection_timeout, то считаем
                # попытку соединения неудачной
                if elapsed_time > connection_timeout:
                    self._is_connected = False
                    break

                ctx.iteration(False)

                if self._is_connected and self._cursor_channel and self._input_channel:
                    break

                gevent.sleep(0.01)  # Даем возможность другим гринлетам выполнятся параллельно
            #
            if self._is_connected:
                # Задержка для эмуляции действия пользователя (?)
                gevent.sleep(random.randint(1, 2))

                # Disconnect
                spice_session.disconnect()
                total_time = self._get_elapsed_time(start_time)
                self.locust_environment.events.request_success.fire(request_type=request_type,
                                                                    name=request_name,
                                                                    response_time=total_time * 1000,
                                                                    response_length=0)
            else:
                raise RuntimeError("Failed to connect.  {}".format(common_except_data))
        except Exception as ex:
            total_time = self._get_elapsed_time(start_time)
            self.locust_environment.events.request_failure.fire(
                request_type=request_type,
                name=request_name,
                response_time=total_time * 1000,
                response_length=0,
                exception=ex
            )
            raise ex

    @staticmethod
    def _get_elapsed_time(start_time):
        return time.time() - start_time

    def _on_channel_new_created(self, session, channel):

        if type(channel) == SpiceClientGLib.MainChannel:
            GObject.GObject.connect(channel, "channel-event", self._on_main_channel_event)
        elif type(channel) == SpiceClientGLib.CursorChannel:
            # print("SpiceClientGLib.CursorChannel")
            self._cursor_channel = channel
        elif type(channel) == SpiceClientGLib.InputsChannel:
            # print("SpiceClientGLib.InputsChannel")
            self._input_channel = channel

    def _on_main_channel_event(self, channel, event):
        # Если главный канал был создан и получил событие OPENED,
        # то это означает успешное спайс соединение
        if event == SpiceClientGLib.ChannelEvent.OPENED:
            self._is_connected = True
