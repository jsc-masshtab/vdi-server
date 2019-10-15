
CONTROLLERS_SUBSCRIPTION = '/controllers/'

CONTROLLER_SUBSCRIPTIONS_LIST = ['/clusters/', '/nodes/', '/data-pools/', '/domains/']
VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST = [*CONTROLLER_SUBSCRIPTIONS_LIST, CONTROLLERS_SUBSCRIPTION]

class SubscriptionCmd:
    add = 'add'
    delete = 'delete'
