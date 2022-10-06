import asyncio
import json
from datetime import datetime, timedelta, timezone

from common.log.journal import system_logger
from common.models.active_tk_connection import ActiveTkConnection
from common.models.settings import Settings
from common.settings import AFK_TIMEOUT, DISCONNECT_INACTIVE_CONNECTIONS, \
    REDIS_THIN_CLIENT_CMD_CHANNEL, WS_PING_TIMEOUT
from common.veil.veil_redis import (
    ThinClientCmd,
    publish_to_redis
)


class ThinClientConnMonitor:
    def __init__(self):
        pass

    def start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.check_for_dead_connections())
        loop.create_task(self.check_for_inactive_connections())

    async def check_for_dead_connections(self):
        """Помечаем  соеднинение завершенным, если от клиента давно не приходило данных."""
        # Вообще это происходит в обработчике ws соединения при его закрытии.
        # Но возможна ситуация когда веб приложение было убито, либо база данных была выключена до
        # веб приложения. Тогда остаются висеть записи, которые мы подчищаем здесь
        # Дельта после достижении которой удаляем данные о неактивном соединении при старле приложения
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
                    message="check_for_dead_connections error.", description=str(ex)
                )

    async def check_for_inactive_connections(self):
        """Завершить неактивные соединения, если того требуют настройки."""
        while True:
            try:
                await asyncio.sleep(10)

                disconnect_inactive_connections = await Settings.get_settings(
                    "DISCONNECT_INACTIVE_CONNECTIONS", DISCONNECT_INACTIVE_CONNECTIONS)
                if not disconnect_inactive_connections:
                    continue

                cur_time = datetime.now(timezone.utc)
                afk_timeout = await Settings.get_settings("AFK_TIMEOUT", AFK_TIMEOUT)
                afk_timeout = timedelta(seconds=afk_timeout)

                inactive_connections = await ActiveTkConnection.query.where(
                    ((cur_time - ActiveTkConnection.last_interaction) > afk_timeout) &  # noqa: W504
                    (ActiveTkConnection.disconnected == None)  # noqa: E711
                ).gino.all()

                for tk_conn in inactive_connections:
                    cmd_dict = dict(command=ThinClientCmd.DISCONNECT.name, conn_id=str(tk_conn.id))
                    await publish_to_redis(REDIS_THIN_CLIENT_CMD_CHANNEL, json.dumps(cmd_dict))

            except asyncio.CancelledError:
                break
            except Exception as ex:
                await system_logger.debug(
                    message="check_for_inactive_connections error.", description=str(ex)
                )
