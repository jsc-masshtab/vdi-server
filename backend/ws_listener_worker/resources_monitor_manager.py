# -*- coding: utf-8 -*-
from controller.models import Controller
from resources_monitor import ResourcesMonitor

from languages import lang_init
from journal.journal import Log as log


_ = lang_init()


class ResourcesMonitorManager:

    def __init__(self):
        self._resources_monitors_list = []

    # PUBLIC METHODS
    async def start(self):
        """
        Start monitors
        :return:
        """
        # log.debug('{}: Startup...'.format(__class__.__name__))
        # get all active controller ips
        controllers_addresses = await Controller.get_addresses()
        msg = _('{cls}: connected controllers -- {controllers}').format(
            cls=__class__.__name__,
            controllers=controllers_addresses)
        log.debug(msg)
        if not controllers_addresses:
            return
        # start resources monitors
        for controller_address in controllers_addresses:
            self._add_monitor_for_controller(controller_address)
        await log.info(_('{}: Started').format(__class__.__name__))

    async def stop(self):
        """
        Stop monitors
        :return:
        """
        for resources_monitor in self._resources_monitors_list:
            await resources_monitor.stop()

    async def add_controller(self, controller_ip):
        # check if controller is already being monitored
        if controller_ip in self._get_monitored_controllers_ips():
            msg = _('{cls}: Controller {ip} is already monitored!').format(
                cls=__class__.__name__,
                ip=controller_ip)
            await log.warning(msg)
            return
        # add monitor
        self._add_monitor_for_controller(controller_ip)
        msg = _('{cls}: resource monitor for controller {ip} connected').format(
            cls=__class__.__name__,
            ip=controller_ip)
        await log.info(msg)

    async def remove_controller(self, controller_ip):
        log.debug(_('Delete controller {} from resources monitor.').format(controller_ip))
        # Деактивируем контроллер
        controller_id = await Controller.get_controller_id_by_ip(controller_ip)
        await Controller.deactivate(controller_id)

        # find resources monitor by controller ip
        try:
            resources_monitor = next(resources_monitor for resources_monitor in self._resources_monitors_list
                                     if resources_monitor.get_controller_ip() == controller_ip)
        except StopIteration:
            msg = _('{cls}: controller {ip} is not monitored!').format(
                cls=__class__.__name__,
                ip=controller_ip)
            log.debug(msg)
            return
        # stop monitoring
        await resources_monitor.stop()
        self._resources_monitors_list.remove(resources_monitor)
        msg = _('{cls}: resource monitor for controller {ip} removed').format(
            cls=__class__.__name__,
            ip=controller_ip)
        await log.warning(msg)

    # PRIVATE METHODS
    def _get_monitored_controllers_ips(self):
        monitored_controllers_ips = [monitor.get_controller_ip() for monitor in self._resources_monitors_list]
        return monitored_controllers_ips

    def _add_monitor_for_controller(self, controller_ip):
        resources_monitor = ResourcesMonitor()
        self._resources_monitors_list.append(resources_monitor)
        resources_monitor.start(controller_ip)

