import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.sql import func

from common.models.active_tk_connection import ActiveTkConnection
from common.settings import WS_PING_TIMEOUT


class ThinClientConnMonitor:
    def __init__(self):
        pass

    async def check_thin_client_connections(self):
        """Помечаем  соеднинение неактивным, если от клиента давно не приходило данных.

        Вообще это происходит в обработчике ws соединения при его закрытии.
        Но возможна ситуация когда веб приложение было убито, либо база данных была выключена до
        веб приложения. Тогда остаются висеть записи, которые мы подчищаем здесь.
        """
        # дельта после достижении которой удаляем данные о неактивном соединении при старле приложения
        # (В иделале на системном уровнем добавить ночную задачу по очистке или что-то типа того)
        delete_time_delta = timedelta(days=14)
        cur_time = datetime.now(timezone.utc)
        await ActiveTkConnection.delete.where(
            (cur_time - ActiveTkConnection.data_received) > delete_time_delta
        ).gino.status()

        while True:
            cur_time = datetime.now(timezone.utc)
            # дельта после достижении которой считаем соединение мертвым
            disconnect_time_delta = timedelta(seconds=WS_PING_TIMEOUT)

            # for debugging
            # conns = await ActiveTkConnection.query.gino.all()
            # if conns:
            #    print('cur_time ', cur_time, flush=True)
            #    print('conns[0].data_received ', conns[0].data_received, flush=True)
            #    diff = cur_time - conns[0].data_received
            #    print('cur_time - conns[0].data_received', diff, flush=True)
            #    print('diff > time_delta', bool(diff > time_delta), flush=True)

            await ActiveTkConnection.update.values(disconnected=func.now()).where(
                (cur_time - ActiveTkConnection.data_received) > disconnect_time_delta
            ).gino.status()

            await asyncio.sleep(WS_PING_TIMEOUT)
