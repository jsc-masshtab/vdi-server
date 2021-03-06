# -*- coding: utf-8 -*-
import asyncio
import json

from yaaredis.exceptions import RedisError

from common.languages import _local_
from common.log.journal import system_logger
from common.models.controller import Controller
from common.settings import REDIS_TIMEOUT, WS_MONITOR_CMD_QUEUE
from common.veil.veil_gino import EntityType
from common.veil.veil_redis import WsMonitorCmd, redis_get_client

from monitor_worker.resources_monitor import ResourcesMonitor


class ResourcesMonitorManager:
    def __init__(self):
        self._resources_monitors_list = []

    # PUBLIC METHODS
    async def listen_for_messages(self):
        """Listen for commands to add/remove controller."""
        await self.start()

        await system_logger.debug("Ws listener worker: start loop now")
        while True:
            try:
                # wait for message
                redis_data = await redis_get_client().redis_blpop(WS_MONITOR_CMD_QUEUE)

                # get data from message
                data_dict = json.loads(redis_data.decode())
                command = data_dict["command"]
                controller_id = data_dict["controller_id"]
                await system_logger.debug(command + " " + controller_id)

                # add or remove controller
                if command == WsMonitorCmd.ADD_CONTROLLER.name:
                    await self.add_controller(controller_id)
                elif command == WsMonitorCmd.REMOVE_CONTROLLER.name:
                    await self.remove_controller(controller_id)
                elif command == WsMonitorCmd.RESTART_MONITOR.name:
                    await self.restart_existing_monitor(controller_id)

            except asyncio.CancelledError:
                raise
            except RedisError as ex:
                await system_logger.debug(
                    message="Redis connection error.", description=str(ex)
                )
                await asyncio.sleep(REDIS_TIMEOUT)
            except Exception as ex:
                entity = {"entity_type": EntityType.SECURITY, "entity_uuid": None}
                if ex:
                    await system_logger.error("exception:" + str(ex), entity=entity)
                else:
                    await system_logger.debug("exception in listen_for_messages.", entity=entity)

    async def start(self):
        """Start monitors."""
        # system_logger.debug('{}: Startup...'.format(__class__.__name__))
        # get all controllers
        controllers = await Controller.query.gino.all()

        controllers_addresses = [controller.address for controller in controllers]
        msg = _local_("{cls}: connected controllers -- {controllers}.").format(
            cls=__class__.__name__, controllers=controllers_addresses
        )
        await system_logger.debug(msg)
        if not controllers:
            return

        # start resources monitors
        for controller in controllers:
            self._add_monitor_for_controller(controller.id)
            await system_logger.debug(
                _local_("{}: Started.").format(__class__.__name__),
                entity=controller.entity
            )

    async def stop(self):
        """Stop monitors.

        :return:
        """
        for resources_monitor in self._resources_monitors_list:
            await resources_monitor.stop()

    async def add_controller(self, controller_id):

        # check if controller is already being monitored
        controller = await Controller.get(controller_id)
        if controller_id in self._get_monitored_controllers_ids():
            msg = _local_("{cls}: Controller {name} is already monitored.").format(
                cls=__class__.__name__, name=controller.verbose_name
            )
            await system_logger.debug(msg, entity=controller.entity)
            return
        # add monitor
        self._add_monitor_for_controller(controller_id)
        msg = _local_(
            "{cls}: resource monitor for controller {name} connected.").format(
            cls=__class__.__name__, name=controller.verbose_name
        )
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

    async def restart_existing_monitor(self, controller_id):

        # find resources monitor by controller ip
        resources_monitor = self._find_monitor_by_controller(controller_id)
        if not resources_monitor:
            return

        await resources_monitor.stop()
        resources_monitor.start(controller_id)

        await system_logger.debug(
            "Resource monitor for controller {} restarted".format(controller_id)
        )

    # PRIVATE METHODS
    def _find_monitor_by_controller(self, controller_id):
        try:
            resources_monitor = next(
                resources_monitor
                for resources_monitor in self._resources_monitors_list
                if str(resources_monitor.get_controller_id()) == str(controller_id)
            )
            return resources_monitor
        except StopIteration:
            return

    def _get_monitored_controllers_ids(self):
        monitored_controllers_ids = [
            monitor.get_controller_id() for monitor in self._resources_monitors_list
        ]
        return monitored_controllers_ids

    def _add_monitor_for_controller(self, controller_id):
        resources_monitor = ResourcesMonitor()
        self._resources_monitors_list.append(resources_monitor)
        resources_monitor.start(controller_id)
