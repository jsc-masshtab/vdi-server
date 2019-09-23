from enum import Enum


ALLOWED_SUBSCRIPTIONS_LIST = ['clusters', 'nodes', 'data-pools', 'domains']


class SubscriptionCmd(Enum):
    ADD = 1
    DELETE = 2
