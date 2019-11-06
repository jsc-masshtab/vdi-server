import json

from resources_monitoring.resources_monitor import ResourcesMonitor, InternalMonitor

from controller_resources.veil_client import ResourcesHttpClient

from controller.models import Controller


class ResourcesMonitorManager:

    def __init__(self):
        self._resources_monitors_list = []
        self._internal_monitor = InternalMonitor()

    # PUBLIC METHODS
    async def start(self):
        """
        Start monitors
        :return:
        """
        print(__class__.__name__, ': Startup...')
        # get all active controller ips
        controllers_addresses = await Controller.get_controllers_addresses()
        print(__class__.__name__, 'connected_controllers', controllers_addresses)
        if not controllers_addresses:
            return
        # start resources monitors
        for controller_address in controllers_addresses:
            await self._add_monitor_for_controller(controller_address)
        print(__class__.__name__, ': Started')

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

        self._internal_monitor.subscribe(observer)

    def unsubscribe(self, observer):
        """
        Unsubscribe observer from all available monitors
        :param observer:
        :return:
        """
        for resources_monitor in self._resources_monitors_list:
            resources_monitor.unsubscribe(observer)

        self._internal_monitor.unsubscribe(observer)

    def add_controller(self, controller_ip):
        # check if controller is already being monitored
        if controller_ip in self._get_monitored_controllers_ips():
            print(__class__.__name__, 'Controller {} is already monitored!'.format(controller_ip))
            return
        # add monitor
        self._add_monitor_for_controller(controller_ip)

    async def remove_controller(self, controller_ip):
        # find resources monitor by controller ip
        try:
            resources_monitor = next(resources_monitor for resources_monitor in self._resources_monitors_list
                                     if resources_monitor.get_controller_ip() == controller_ip)
        except StopIteration:
            print(__class__.__name__, 'Controller {} is not monitored!'.format(controller_ip))
            return
        # stop monitoring
        await resources_monitor.stop()
        self._resources_monitors_list.remove(resources_monitor)

    def signal_internal_event(self, msg_dict):
        """
        Notify observers about internal event
        """
        print(msg_dict)
        json_data = json.dumps(msg_dict)
        self._internal_monitor.signal_event(json_data)

    # PRIVATE METHODS
    def _get_monitored_controllers_ips(self):
        monitored_controllers_ips = [monitor.get_controller_ip() for monitor in self._resources_monitors_list]
        return monitored_controllers_ips

    async def _add_monitor_for_controller(self, controller_ip):
        resources_monitor = ResourcesMonitor()
        self._resources_monitors_list.append(resources_monitor)
        await resources_monitor.start(controller_ip)


resources_monitor_manager = ResourcesMonitorManager()
