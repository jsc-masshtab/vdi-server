import json

from resources_monitoring.resources_monitor import ResourcesMonitor, InternalMonitor
#from ..tasks.resources import DiscoverControllers

from controller_resources.veil_client import ResourcesHttpClient


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
        resources_http_client = ResourcesHttpClient()
        connected_controllers = await resources_http_client.discover_controllers(return_broken=False)
        print(__class__.__name__, 'connected_controllers', connected_controllers)
        if not connected_controllers:
            return
        # start resources monitors
        for controller in connected_controllers:
            self._add_monitor_for_controller(controller['address'])
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

    def _add_monitor_for_controller(self, controller_ip):
        resources_monitor = ResourcesMonitor()
        self._resources_monitors_list.append(resources_monitor)
        resources_monitor.start(controller_ip)


resources_monitor_manager = ResourcesMonitorManager()
