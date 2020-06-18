# -*- coding: utf-8 -*-
from abc import ABC


class AbstractMonitor(ABC):

    def __init__(self):
        self._list_of_observers = []

    # PUBLIC METHODS
    def subscribe(self, observer):
        if observer not in self._list_of_observers:
            self._list_of_observers.append(observer)

    def unsubscribe(self, observer):
        if observer in self._list_of_observers:
            self._list_of_observers.remove(observer)

    def unsubscribe_all(self):
        self._list_of_observers.clear()

    def notify_observers(self, sub_source, json_data):
        for observer in self._list_of_observers:
            if sub_source in observer.get_subscriptions():
                observer.on_notified(json_data)
