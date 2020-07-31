# -*- coding: utf-8 -*-
import asyncio
import json

from common.database import start_gino, stop_gino
from ws_listener_worker.resources_monitor_manager import ResourcesMonitorManager
from common.veil.veil_redis import REDIS_POOL, WS_MONITOR_CHANNEL_IN, REDIS_CLIENT, WsMonitorCmd, a_redis_get_message

from common.languages import lang_init
from common.log.journal import system_logger
from common.utils import init_exit_handler

_ = lang_init()


# cli fast test: PUBLISH WS_MONITOR_CHANNEL_IN '{"command": "ADD_CONTROLLER", "controller_address": "192.168.9.145"}'
async def listen_for_messages(resources_monitor_manager):
    """Listen for commands to add/remove controller"""
    await resources_monitor_manager.start()

    redis_subscriber = REDIS_CLIENT.pubsub()
    redis_subscriber.subscribe(WS_MONITOR_CHANNEL_IN)

    await system_logger.warning(_('Ws listener worker: start loop now'))
    while True:
        try:
            # wait for message
            redis_message = await a_redis_get_message(redis_subscriber)

            if redis_message['type'] != 'message':
                continue

            await system_logger.warning('redis_message' + str(redis_message))

            # get data from message
            data_dict = json.loads(redis_message['data'].decode())
            command = data_dict['command']
            controller_id = data_dict['controller_id']
            await system_logger.warning(command + ' ' + controller_id)

            # add or remove controller
            if command == WsMonitorCmd.ADD_CONTROLLER.name:
                await resources_monitor_manager.add_controller(controller_id)
            elif command == WsMonitorCmd.REMOVE_CONTROLLER.name:
                await resources_monitor_manager.remove_controller(controller_id)
            elif command == WsMonitorCmd.RESTART_MONITOR.name:
                await resources_monitor_manager.restart_existing_monitor(controller_id)

        except asyncio.CancelledError:
            raise
        except Exception as ex:
            await system_logger.error('exception:' + str(ex))


def main():
    init_exit_handler()

    loop = asyncio.get_event_loop()

    # init gino
    loop.run_until_complete(start_gino())

    resources_monitor_manager = ResourcesMonitorManager()

    loop.create_task(listen_for_messages(resources_monitor_manager))

    loop.run_forever()  # run until event loop stop

    system_logger._debug("Ws listener worker stopped")
    # free resources
    loop.run_until_complete(resources_monitor_manager.stop())
    REDIS_POOL.disconnect()
    loop.run_until_complete(stop_gino())


if __name__ == '__main__':
    main()
