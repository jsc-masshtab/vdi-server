# -*- coding: utf-8 -*-
POOLS_SUBSCRIPTION = '/pools/'
# subscription to receive events
EVENTS_SUBSCRIPTION = '/events/'
# subscription to receive controller status
CONTROLLERS_SUBSCRIPTION = '/controllers/'
# subscription to receive VDI related task data
VDI_TASKS_SUBSCRIPTION = '/vdi_tasks/'
# subscriptions to receive data from controller
CONTROLLER_SUBSCRIPTIONS_LIST = ['/clusters/', '/resource_pools/', '/nodes/', '/data-pools/', '/domains/', '/tasks/']
# subscriptions to data which VDI front can receive from VDI back
VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST = [*CONTROLLER_SUBSCRIPTIONS_LIST,
                                        POOLS_SUBSCRIPTION,
                                        EVENTS_SUBSCRIPTION,
                                        CONTROLLERS_SUBSCRIPTION,
                                        VDI_TASKS_SUBSCRIPTION]


class SubscriptionCmd:
    add = 'add'
    delete = 'delete'
