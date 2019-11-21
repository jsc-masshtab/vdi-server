from vm.models import Vm
from pool.models import Pool
from database import db


class VmManager:
    """Я правильно понял что делать так: На VDI сервере в корутине постоянно проверяем запущены
        ли машины имеющие пользователя. Если какая-то машине не запущена, то запускаем.
        В бд в таблице пулов нужно ввести булевый столбец держать машины включеными или нет."""

    def __init__(self):
        pass

    async def start(self):
        # get vms with user
        #vms_ids = await Vm.get_all_occupied_vms_ids()

        query = await db.select([Vm, Pool]).select_from(Vm.join(Pool, isouter=True)).group_by(
            Vm.id, Pool.keep_vms_on).where((Vm.username is not None)).gino.all()

        print(__class__.__name__, ' query', query)

