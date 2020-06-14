# -*- coding: utf-8 -*-
from resources_monitoring.resources_monitoring_data import VDI_TASKS_SUBSCRIPTION, EVENTS_SUBSCRIPTION
from resources_monitoring.abstract_event_monitor import AbstractMonitor

# Вместо этого тупо канал в редисе

# class InternalMonitor(AbstractMonitor):
#     """
#     monitoring of internal VDI events (pool progress creation, result of pool creation...)
#     """
#
#     def __init__(self):
#         super().__init__()
#
#     # PUBLIC METHODS
#     def signal_event(self, json_data):
#         self.notify_observers(VDI_TASKS_SUBSCRIPTION, json_data)
#
#     def signal_event_2(self, json_data):
#         self.notify_observers(EVENTS_SUBSCRIPTION, json_data)
#
#
# internal_event_monitor = InternalMonitor()
