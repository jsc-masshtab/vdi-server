import asyncio
from datetime import timedelta, datetime, timezone

from common.settings import WS_PING_TIMEOUT

from common.models.active_tk_connection import ActiveTkConnection
from common.log.journal import system_logger


class ThinClientConnMonitor:

    def __init__(self):
        pass

    async def check_thin_client_connections(self):
        """Удаляем информацию о соеднинении если от клиента давно не приходило данных.
        Вообще это удаление просиходит в обработчике ws соединения при его закрытии.
        Но возможна ситуация когда веб приложение было убито, либо база данных была выключена до
        веб приложения. Тогда остаются висеть записи, которые мы подчищаем здесь"""

        while True:
            cur_time = datetime.now(timezone.utc)
            time_delta = timedelta(seconds=WS_PING_TIMEOUT)  # WS_PING_TIMEOUT

            # for debugging
            # conns = await ActiveTkConnection.query.gino.all()
            # if conns:
            #    print('cur_time ', cur_time, flush=True)
            #    print('conns[0].data_received ', conns[0].data_received, flush=True)
            #    diff = cur_time - conns[0].data_received
            #    print('cur_time - conns[0].data_received', diff, flush=True)
            #    print('diff > time_delta', bool(diff > time_delta), flush=True)

            st = await ActiveTkConnection.delete.where(
                (cur_time - ActiveTkConnection.data_received) > time_delta).gino.status()
            if st:
                system_logger._debug('Some dead thin client connection records removed')

            await asyncio.sleep(WS_PING_TIMEOUT)
