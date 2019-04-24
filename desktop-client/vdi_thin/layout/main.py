import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf

import logging
LOG = logging.getLogger()

from vdi_thin.commands.start_vm import StartVmCommand
from vdi_thin.commands.load_vms import LoadVms


class Main(Gtk.ApplicationWindow):
    def __init__(self, app):
        super(Main, self).__init__()
        LOG.debug("init_main")
        self.app = app
        self.set_application(app)
        self.set_can_focus(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_default_geometry(640, 480)
        self.set_title(app.NAME_MANAGER)
        self.set_icon(app.LOGO)
        self.set_has_resize_grip(True)
        self.connect("delete-event", self.on_main_window_delete_event)
        self.connect("show", self.on_main_window_show)

        vbox = Gtk.VBox()

        hbox = Gtk.HBox(False, 0)

        logout_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_DISCONNECT))
        logout_button.set_always_show_image(True)
        logout_button.set_label("Logout")
        logout_button.connect("clicked", self.on_logout_button_clicked)
        hbox.pack_end(logout_button, False, False, 0)

        refresh_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_REFRESH))
        refresh_button.set_always_show_image(True)
        refresh_button.set_label("Refresh")
        refresh_button.connect("clicked", self.on_refresh_button_clicked)
        hbox.pack_start(refresh_button, False, False, 0)

        vbox.pack_start(hbox, False, False, 0)

        mbox = Gtk.Box()

        main_content = Gtk.ScrolledWindow()

        view_port = Gtk.Viewport()

        vpbox = Gtk.VBox()

        self.main_content_flowbox = Gtk.FlowBox()
        self.main_content_flowbox.set_can_focus(False)
        self.main_content_flowbox.set_margin_top(10)
        self.main_content_flowbox.set_margin_right(10)
        self.main_content_flowbox.set_margin_bottom(10)
        self.main_content_flowbox.set_margin_left(10)
        self.main_content_flowbox.set_column_spacing(10)
        self.main_content_flowbox.set_row_spacing(10)
        self.main_content_flowbox.set_max_children_per_line(10)
        vpbox.pack_start(self.main_content_flowbox, False, True, 0)

        self.load_spinner = Gtk.Spinner()
        vpbox.pack_start(self.load_spinner, True, True, 1)

        view_port.add(vpbox)

        main_content.add(view_port)

        mbox.pack_start(main_content, True, True, 0)

        vbox.pack_start(mbox, True, True, 1)

        self.periodic_refresh = None

        self.add(vbox)
        self.show_all()

    def on_main_window_delete_event(self, *args):
        LOG.debug("quit confirm cancel")
        if self.app.confirm_quit():
            self.app.do_quit()
        else:
            return True

    def on_logout_button_clicked(self, *args):
        if self.app.confirm_logout():
            self.app.do_logout()

    def on_refresh_button_clicked(self, *args):
        LOG.debug("refresh button clicked")
        self.load_vms()

    def on_main_window_show(self, *args):
        self.load_vms()

    def load_vms(self, show_spinner=True):
        if show_spinner:
            self.load_spinner.start()
        cmd = LoadVms(self.app, on_finish=self.on_vm_load_finish)
        cmd()

    def on_vm_load_finish(self, ctx, result):
        self.register_vm_widgets(result)
        self.main_content_flowbox.show_all()
        self.main_content_flowbox.set_visible(True)
        self.load_spinner.stop()

    def register_vm_widgets(self, vm_data):
        widget_gen = VmWidgetGenerator(self.app)
        self.main_content_flowbox.forall(lambda w: self.main_content_flowbox.remove(w))
        for vm in vm_data:
            vm_widget = widget_gen.generate_widget(vm,
                                                   self.on_vm_widget_connect_clicked)
            self.main_content_flowbox.add(vm_widget)

    def on_vm_widget_connect_clicked(self, elem, vm_widget):
        cmd = StartVmCommand(self.app,
                             vm_widget=vm_widget,
                             on_finish=self.on_vm_connect)
        vm_widget.wait_state()
        cmd(vm_widget.dp_id)

    def on_vm_connect(self, context, result):
        self.app.do_viewer(host=result['host'], port=result['port'], password=result['password'])


class VmWidget(Gtk.Frame):
    WIDGET_HEIGHT = 100
    WIDGET_WIDTH = 100

    def __init__(self, app, vm_data, icon, start_handler, *args, **kwargs):
        super(VmWidget, self).__init__(*args, **kwargs)
        self.connect_btn = None
        self.app = app
        self.dp_id = vm_data["id"]
        self.vm_data = vm_data
        self.icon = icon
        self.screenshot = None
        self.wait_spinner = Gtk.Spinner()
        self.dimmer = self.build_content_dim()
        self.start_handler = start_handler
        self.vm_repr = self.build_vm_repr()
        self.base_layout = self.build_base_layout(self.vm_repr)
        self.add(self.base_layout)

    def on_show(self, *args):
        self.normal_state()

    def wait_state(self):
        self.dimmer.set_visible(True)
        self.wait_spinner.start()

    def normal_state(self):
        self.wait_spinner.stop()
        self.dimmer.set_visible(False)

    def build_base_layout(self, vm_repr):
        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        base_box.set_size_request(self.WIDGET_WIDTH, self.WIDGET_HEIGHT)
        overlay = Gtk.Overlay()
        overlay.add(vm_repr)
        overlay.add_overlay(self.wait_spinner)
        overlay.add_overlay(self.dimmer)
        overlay.set_overlay_pass_through(self.wait_spinner, True)
        overlay.set_overlay_pass_through(self.dimmer, True)
        base_box.pack_start(overlay, True, True, 0)
        base_box.connect("show", self.on_show)
        return base_box

    def build_content_dim(self):
        da = Gtk.DrawingArea()
        da.set_opacity(0.3)
        da.connect('draw', self.dim_draw_signal)
        return da

    def dim_draw_signal(self, da, ctx):
        ctx.rectangle(0, 0, da.get_allocated_width(), da.get_allocated_height())
        ctx.fill()

    def build_action_button(self, action):
        btn = Gtk.Button.new_from_stock(Gtk.STOCK_CONNECT)
        btn.set_always_show_image(True)
        btn.connect("clicked", action, self)
        btn.set_margin_start(10)
        btn.set_margin_end(10)
        btn.set_margin_bottom(10)
        return btn

    def build_vm_repr(self):
        self.connect_btn = self.build_action_button(self.start_handler)
        vm_repr = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vm_name = Gtk.Label.new(str(self.vm_data["name"]))
        vm_name.set_margin_top(10)
        if not self.vm_data["can_start_vm"]:
            self.connect_btn.set_sensitive(False)
        vm_repr.pack_start(vm_name, True, True, 0)
        vm_repr.pack_start(self.icon, True, True, 0)
        vm_repr.pack_start(self.connect_btn, True, True, 0)
        return vm_repr


class VmWidgetGenerator:
    def __init__(self, app):
        self.app = app
        self._pix_buf_cache = {}

    def get_windows_icon(self):
        return self.build_os_img("content/img/windows_icon.png")

    def get_linux_icon(self):
        return self.build_os_img("content/img/linux_icon.png")

    def get_other_icon(self):
        return self.build_os_img("content/img/other_icon.png")

    def build_os_img(self, icon_path):
        return self.build_img(icon_path, 50, 50)

    def build_img(self, icon_path, width, height):
        cache_key = "{}:{}:{}".format(icon_path, width, height)
        image = Gtk.Image()
        pixbuf = self._pix_buf_cache.get(cache_key)
        if not pixbuf:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
            pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.HYPER)
            self._pix_buf_cache[cache_key] = pixbuf
        image.set_from_pixbuf(pixbuf)
        return image

    def select_vm_icon(self, vm_data):
        icon_map = {"LINUX": self.get_linux_icon,
                    "WIN": self.get_windows_icon,
                    "OTHER": self.get_other_icon}
        try:
            return icon_map[vm_data["os"]]()
        except KeyError:
            return icon_map["OTHER"]()

    def generate_widget(self, vm_data, start_handler):
        vm_icon = self.select_vm_icon(vm_data)
        widget = VmWidget(self.app, vm_data, vm_icon, start_handler)
        return widget

