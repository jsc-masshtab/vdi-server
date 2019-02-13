

import asyncio
import contextvars


class Tasks:
    _tasks = contextvars.ContextVar('tasks')

    def __contains__(self, item):
        return item in self._tasks.get()

    def __getitem__(self, key):
        tasks = self._tasks.get()
        if key in tasks:
            task = tasks[key]
            return task
        loop = asyncio.events.get_event_loop()
        tasks[key] = loop.create_future()
        return tasks[key]


class Context:
    values = contextvars.ContextVar('values')
    tasks = Tasks()

    def __getattr__(self, item):
        return self.values.get()[item]

    def set_attr(self, key, value):
        values = self.values.get()
        values[key] = value

    def init(self):
        self.values.set({})
        self.tasks._tasks.set({})


g = Context()

# a decorator
def task(co):
    return Task.from_co(co)

class Task:

    _source = 'class'

    def __await__(self):
        return self.ensure_task().__await__()

    @classmethod
    def from_co(cls, f):
        # TODO check no params
        obj = cls()
        obj._co = f
        obj._source = 'co'
        return obj

    @property
    def id(self):
        if self._source == 'class':
            return self.__class__
        assert self._source == 'co'
        return self._co

    @property
    def co(self):
        if self._source == 'class':
            return self.run
        assert self._source == 'co'
        return self._co

    def ensure_task(self):
        tasks = g.tasks._tasks.get()
        if self.id in tasks:
            return tasks[self.id]
        task = asyncio.create_task(self.co())
        task = asyncio.shield(task)
        tasks[self.id] = task
        return task

    def __call__(self):
        return self