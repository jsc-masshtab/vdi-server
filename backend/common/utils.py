import re
import asyncio
import signal
import functools

from enum import Enum


def clamp_value(my_value, min_value, max_value):
    """
    limit value by min_value and max_value
    """
    return max(min(my_value, max_value), min_value)


def validate_name(name_string):
    """
    validate if name correct
    """
    return re.match("^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$", name_string)


async def cancel_async_task(async_task, wait_for_result=True):
    if async_task:
        try:
            async_task.cancel()
            if wait_for_result:
                await async_task
        except asyncio.CancelledError:
            pass


def extract_ordering_data(ordering):
    reverse = ordering.find("-", 0, 1) == 0
    if reverse:
        ordering = ordering[1:]
    return ordering, reverse


def init_signals(sig_handler):
    """Set exit handler"""
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)


def init_exit_handler():
    async def _shutdown(sig, loop):

        try:
            print("Caught signal {0}".format(sig.name))
            tasks = [
                task
                for task in asyncio.Task.all_tasks()
                if task is not asyncio.tasks.Task.current_task()
            ]
            list(map(lambda task: task.cancel(), tasks))

            results_future = asyncio.gather(*tasks, return_exceptions=True)
            # Был случай, что вернулось не future, поэтому проверяем.
            if asyncio.isfuture(results_future):
                results = await results_future
                print("finished awaiting cancelled tasks, results: {0}".format(results))

        finally:
            loop.stop()

    # init handlers
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(
        signal.SIGTERM,
        functools.partial(asyncio.ensure_future, _shutdown(signal.SIGTERM, loop)),
    )
    loop.add_signal_handler(
        signal.SIGINT,
        functools.partial(asyncio.ensure_future, _shutdown(signal.SIGINT, loop)),
    )


def gino_model_to_json_serializable_dict(model):
    """Gino модель в словарь для json
       Возможно по питоновским понятиям лучше создать  mixin и добавить его в модели"""
    mode_dict = model.to_dict()
    json_serializable_dict = dict()

    for key, value in mode_dict.items():
        if isinstance(value, Enum):
            json_serializable_dict[key] = value.name
        elif isinstance(value, str):
            if key != "token" and key != "password":
                json_serializable_dict[key] = value
        else:
            json_serializable_dict[key] = str(value)

    return json_serializable_dict


def convert_gino_model_to_graphene_type(model, graphene_custom_type):
    """Тот редкий случай, когда модель и граф ql тип совпадают"""
    data_dict = dict()
    for model_atr_key in model.__dict__["__values__"]:
        if model_atr_key in graphene_custom_type.__dict__.keys():
            val = getattr(model, model_atr_key)
            data_dict[model_atr_key] = val

    return graphene_custom_type(**data_dict)
