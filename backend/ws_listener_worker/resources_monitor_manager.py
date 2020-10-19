# -*- coding: utf-8 -*-
from common.models.controller import Controller
from ws_listener_worker.resources_monitor import ResourcesMonitor

from common.languages import lang_init
from common.log.journal import system_logger


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
        # system_logger.debug('{}: Startup...'.format(__class__.__name__))
        # get all controllers
        controllers = await Controller.query.gino.all()

        controllers_addresses = [controller.address for controller in controllers]
        msg = _('{cls}: connected controllers -- {controllers}').format(
            cls=__class__.__name__,
            controllers=controllers_addresses)
        await system_logger.debug(msg)
        if not controllers:
            return

        # start resources monitors
        for controller in controllers:
            self._add_monitor_for_controller(controller.id)
            await system_logger.debug(_('{}: Started').format(__class__.__name__), entity=controller.entity)

    async def stop(self):
        """
        Stop monitors
        :return:
        """
        for resources_monitor in self._resources_monitors_list:
            await resources_monitor.stop()

    async def add_controller(self, controller_id):

        # check if controller is already being monitored
        controller = await Controller.get(controller_id)
        if controller_id in self._get_monitored_controllers_ids():
            msg = _('{cls}: Controller {name} is already monitored!').format(
                cls=__class__.__name__,
                name=controller.verbose_name)
            await system_logger.debug(msg, entity=controller.entity)
            return
        # add monitor
        self._add_monitor_for_controller(controller_id)
        msg = _('{cls}: resource monitor for controller {name} connected').format(
            cls=__class__.__name__,
            name=controller.verbose_name)
        await system_logger.debug(msg, entity=controller.entity)

    async def remove_controller(self, controller_id):
        # controller = await Controller.get(controller_id)
        # await system_logger.debug(_('Delete controller {} from resources monitor.').format(controller_id))

        # find resources monitor by controller ip
        resources_monitor = self._find_monitor_by_controller(controller_id)
        if not resources_monitor:
            return

        # stop monitoring
        await resources_monitor.stop()
        self._resources_monitors_list.remove(resources_monitor)

        # msg = _('{cls}: resource monitor for controller {name} removed').format(
        #     cls=__class__.__name__,
        #     name=controller.verbose_name)
        # await system_logger.debug(msg)

    async def restart_existing_monitor(self, controller_id):

        # find resources monitor by controller ip
        resources_monitor = self._find_monitor_by_controller(controller_id)
        if not resources_monitor:
            return

        await resources_monitor.stop()
        resources_monitor.start(controller_id)

    # PRIVATE METHODS
    def _find_monitor_by_controller(self, controller_id):
        try:
            resources_monitor = next(resources_monitor for resources_monitor in self._resources_monitors_list
                                     if str(resources_monitor.get_controller_id()) == str(controller_id))
            return resources_monitor
        except StopIteration:
            msg = _('{cls}: controller {id} is not monitored!').format(
                cls=__class__.__name__,
                id=controller_id)
            system_logger._debug(msg)
            return None

    def _get_monitored_controllers_ids(self):
        monitored_controllers_ids = [monitor.get_controller_id() for monitor in self._resources_monitors_list]
        return monitored_controllers_ids

    def _add_monitor_for_controller(self, controller_id):
        resources_monitor = ResourcesMonitor()
        self._resources_monitors_list.append(resources_monitor)
        resources_monitor.start(controller_id)
