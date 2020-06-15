# -*- coding: utf-8 -*-
import asyncio
import json

from database import start_gino, stop_gino

from resources_monitor_manager import ResourcesMonitorManager

from redis_broker import REDIS_POOL, WS_MONITOR_CHANNEL_IN, REDIS_CLIENT, WsMonitorCmd, a_redis_get_message

from languages import lang_init
from journal.journal import Log as log

_ = lang_init()


async def listen_for_messages(resources_monitor_manager):

    await resources_monitor_manager.start()

    log.general(_('Ws listener worker: start loop now'))
    while True:
        try:
            # wait for message
            redis_subscriber = REDIS_CLIENT.pubsub()
            redis_subscriber.subscribe(WS_MONITOR_CHANNEL_IN)

            redis_message = await a_redis_get_message(redis_subscriber)
            print("redis_message", redis_message)
            # get data from message
            command = redis_message['command']
            address = redis_message['controller_address']

            # add or remove controller
            if command == WsMonitorCmd.ADD_CONTROLLER:
                await resources_monitor_manager.add_controller(address)
            elif command == WsMonitorCmd.REMOVE_CONTROLLER:
                await resources_monitor_manager.remove_controller(address)

        except Exception as ex:
            await log.error(str(ex))


def main():
    loop = asyncio.get_event_loop()

    # init gino
    loop.run_until_complete(start_gino())

    resources_monitor_manager = ResourcesMonitorManager()

    try:
        loop.create_task(listen_for_messages(resources_monitor_manager))
        loop.run_forever()
    except KeyboardInterrupt:
        log.general(_("Ws listener worker interrupted"))
    finally:
        # free resources
        loop.run_until_complete(resources_monitor_manager.stop())
        REDIS_POOL.disconnect()
        loop.run_until_complete(stop_gino())


if __name__ == '__main__':
    main()
