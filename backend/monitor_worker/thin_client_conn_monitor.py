import asyncio
from datetime import datetime, timedelta, timezone

from common.log.journal import system_logger
from common.models.active_tk_connection import ActiveTkConnection
from common.settings import WS_PING_TIMEOUT


class ThinClientConnMonitor:
    def __init__(self):
        pass

    async def check_thin_client_connections(self):
        """Помечаем  соеднинение неактивным, если от клиента давно не приходило данных."""
        # Вообще это происходит в обработчике ws соединения при его закрытии.
        # Но возможна ситуация когда веб приложение было убито, либо база данных была выключена до
        # веб приложения. Тогда остаются висеть записи, которые мы подчищаем здесь
        # Дельта после достижении которой удаляем данные о неактивном соединении при старле приложения
        # (В иделале на системном уровнем добавить ночную задачу по очистке или что-то типа того)
        delete_time_delta = timedelta(days=365)

        cur_time = datetime.now(timezone.utc)
        await ActiveTkConnection.delete.where(
            (cur_time - ActiveTkConnection.data_received) > delete_time_delta
        ).gino.status()

        # дельта после достижении которой считаем соединение мертвым
        disconnect_time_delta = timedelta(seconds=WS_PING_TIMEOUT)

        while True:
            try:
                cur_time = datetime.now(timezone.utc)

                tk_connections_to_deactivate = await ActiveTkConnection.query.where(
                    ((cur_time - ActiveTkConnection.data_received) > disconnect_time_delta) &  # noqa: W504
                    (ActiveTkConnection.disconnected == None)  # noqa: E711
                ).gino.all()

                for tk_conn in tk_connections_to_deactivate:
                    await tk_conn.deactivate(dead_connection_detected=True)

                await asyncio.sleep(WS_PING_TIMEOUT)

            except asyncio.CancelledError:
                break
            except Exception as ex:
                await system_logger.debug(
                    message="check_thin_client_connections error.", description=str(ex)
                )
