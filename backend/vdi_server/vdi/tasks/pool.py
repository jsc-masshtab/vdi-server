
from dataclasses import dataclass
from classy_async.g_tasks import Var



@dataclass()
class PoolSettings(Var):
    controller_ip: str
    cluster_id: str
    datapool_id: str