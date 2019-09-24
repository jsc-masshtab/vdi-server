from vdi.resources_monitoring.resources_monitor import ResourcesMonitor
from db.db import db
from ..tasks.resources import DiscoverControllers


class ResourcesMonitorManager:
    # ATTRIBUTES
    _resources_monitors_list = []

    # PUBLIC METHODS
    async def start(self):
        """
        Start monitors
        :return:
        """
        print(__class__.__name__, ': Startup...')
        # get all active controller ips
        connected_controllers = await DiscoverControllers(return_broken=False)
        print(__class__.__name__, 'connected_controllers', connected_controllers)
        if not connected_controllers:
            return

        # start resources monitors
        for controller in connected_controllers:
            resources_monitor = ResourcesMonitor()
            self._resources_monitors_list.append(resources_monitor)
            resources_monitor.start(controller['ip'])

        # resources_monitor = ResourcesMonitor()
        # self._resources_monitors_list.append(resources_monitor)
        # resources_monitor.start('')

    async def stop(self):
        """
        Stop monitors
        :return:
        """
        for resources_monitor in self._resources_monitors_list:
            await resources_monitor.stop()

    def subscribe(self, observer):
        """
        Subscribe observer to all available monitors
        :param observer:
        :return:
        """
        for resources_monitor in self._resources_monitors_list:
            resources_monitor.subscribe(observer)

    def unsubscribe(self, observer):
        """
        Unsubscribe observer from all available monitors
        :param observer:
        :return:
        """
        for resources_monitor in self._resources_monitors_list:
            resources_monitor.unsubscribe(observer)

    # PRIVATE METHODS


resources_monitor_manager = ResourcesMonitorManager()
