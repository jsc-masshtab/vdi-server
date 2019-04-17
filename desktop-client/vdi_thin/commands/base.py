#!/usr/bin/env python
# -*- coding: utf-8 -*-



import logging

try:
    import queue
except ModuleNotFoundError:
    import Queue as queue

import threading
import time

from gi.repository import GLib
from multiprocessing import Process, Queue, Event

from ..services.api_session import ApiConnectionError, ApiUnknownError

LOG = logging.getLogger()


class AsyncCallPromise:
    def __init__(self, cmd_id, control_thread, force_stop_event, worker_process):
        self.id = cmd_id
        self.control_thread = control_thread
        self.force_stop_event = force_stop_event
        self.worker_process = worker_process

    def is_ready(self):
        return not self.control_thread.is_alive()

    def _terminate_worker_process(self):
        self.worker_process.terminate()
        self.control_thread.join()

    def cancel(self):
        self._terminate_worker_process()

    def force_stop(self):
        self.force_stop_event.set()
        self._terminate_worker_process()


class AsyncCallCmd:
    def __init__(self, app, on_finish=None,
                 on_exception=None, on_cancel=None, api_session=None, **kwargs):
        self.app = app
        self.api_session = api_session or self.app.api_session
        self.on_finish = on_finish or self.on_finish
        self.on_cancel = on_cancel or self.on_cancel
        self.on_exception = on_exception or self.on_exception
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        p_queue = queue.Queue()
        stop_event = threading.Event()
        t = threading.Thread(target=self.control_thread_wrapper,
                             args=(p_queue, stop_event) + tuple(args),
                             kwargs=kwargs)
        t.start()
        p = p_queue.get(block=True)
        promise = AsyncCallPromise(cmd_id=t.ident,
                                   control_thread=t,
                                   force_stop_event=stop_event,
                                   worker_process=p)
        self.app.register_worker_promise(promise)
        return promise

    def on_finish(self, context, r):
        raise NotImplementedError

    def on_cancel(self, context):
        raise NotImplementedError

    def on_exception(self, context, e):
        raise NotImplementedError# from e

    def get_context_data(self):
        return self.kwargs

    def control_thread_wrapper(self, p_queue, stop_event, *args, **kwargs):
        q = Queue()
        exception_q = Queue()
        # finish_event необходим для определения была ли задача отменена
        finish_event = Event()
        p = Process(target=self.cmd_wrapper,
                    args=(q, exception_q, finish_event) + tuple(args),
                    kwargs=kwargs)
        p.start()
        p_queue.put(p)
        p.join()
        if stop_event.is_set():
            return
        if finish_event.is_set():
            exception = self._non_block_queue_read(exception_q)
            if exception:
                GLib.idle_add(self.on_exception, self.get_context_data(), exception)
            else:
                GLib.idle_add(self.on_finish,
                              self.get_context_data(), self._non_block_queue_read(q))
        else:
            GLib.idle_add(self.on_cancel, self.get_context_data())
        self.app.unregister_worker_promise(self.get_promise_id())

    def get_promise_id(self):
        return threading.current_thread().ident

    def _non_block_queue_read(self, q):
        try:
            return q.get(block=False)
        except queue.Empty:
            return None

    def cmd_wrapper(self, q, exception_q, finish_event, *args, **kwargs):
        try:
            r = self.run(*args, **kwargs)
            q.put(r)
        except Exception as e:
            LOG.exception("CMD run exception")
            exception_q.put(e)
        LOG.debug("set finish event")
        finish_event.set()

    def run(self, *args, **kwargs):
        raise NotImplementedError("Please implement this method")

    def retry(self, retry_count, retry_interval, func, arg=None, kwarg=None):
        for n in range(retry_count):
            try:
                arg = arg or tuple()
                kwarg = kwarg or dict()
                return func(*arg, **kwarg)
            except ApiConnectionError:
                time.sleep(retry_interval)
                continue
        raise ApiConnectionError

    def wait_job(self, job_id):
        while True:
            job_data = self.api_session.get_job(job_id)
            if job_data["ready"]:
                if job_data["error"]:
                    raise ApiUnknownError
                return True
            time.sleep(2)
