from controller.models import Controller
from event.models import Event
from resources_monitoring.resources_monitor import ResourcesMonitor


# TODO: выделить функционал подписок
class ResourcesMonitorManager:

    def __init__(self):
        self._resources_monitors_list = []

    # PUBLIC METHODS
    async def start(self):
        """
        Start monitors
        :return:
        """
        print(__class__.__name__, ': Startup...')
        # get all active controller ips
        controllers_addresses = await Controller.get_controllers_addresses()
        msg = '{cls}: connected controllers -- {controllers}'.format(
            cls=__class__.__name__,
            controllers=controllers_addresses)
        await Event.create_info(msg)
        if not controllers_addresses:
            return
        # start resources monitors
        for controller_address in controllers_addresses:
            self._add_monitor_for_controller(controller_address)
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

        #self._internal_monitor.subscribe(observer)

    def unsubscribe(self, observer):
        """
        Unsubscribe observer from all available monitors
        :param observer:
        :return:
        """
        for resources_monitor in self._resources_monitors_list:
            resources_monitor.unsubscribe(observer)

        #self._internal_monitor.unsubscribe(observer)

    async def add_controller(self, controller_ip):
        # check if controller is already being monitored
        if controller_ip in self._get_monitored_controllers_ips():
            msg = '{cls}: Controller {ip} is already monitored!'.format(
                cls=__class__.__name__,
                ip=controller_ip)
            await Event.create_warning(msg)
            return
        # add monitor
        self._add_monitor_for_controller(controller_ip)
        msg = '{cls}: resource monitor for controller {ip} connected'.format(
            cls=__class__.__name__,
            ip=controller_ip)
        await Event.create_info(msg)

    async def remove_controller(self, controller_ip):
        # find resources monitor by controller ip
        try:
            resources_monitor = next(resources_monitor for resources_monitor in self._resources_monitors_list
                                     if resources_monitor.get_controller_ip() == controller_ip)
        except StopIteration:
            msg = '{cls}: controller {ip} is not monitored!'.format(
                cls=__class__.__name__,
                ip=controller_ip)
            await Event.create_error(msg)
            return
        # stop monitoring
        await resources_monitor.stop()
        self._resources_monitors_list.remove(resources_monitor)
        msg = '{cls}: resource monitor for controller {ip} removed'.format(
            cls=__class__.__name__,
            ip=controller_ip)
        await Event.create_info(msg)

    # PRIVATE METHODS
    def _get_monitored_controllers_ips(self):
        monitored_controllers_ips = [monitor.get_controller_ip() for monitor in self._resources_monitors_list]
        return monitored_controllers_ips

    def _add_monitor_for_controller(self, controller_ip):
        resources_monitor = ResourcesMonitor()
        self._resources_monitors_list.append(resources_monitor)
        resources_monitor.start(controller_ip)


resources_monitor_manager = ResourcesMonitorManager()