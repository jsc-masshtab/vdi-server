
from classy_async.classy_async import Task
from starlette.requests import Request as _Request

class RequestTask(Task):
    return_value = None  # _Request

    async def run(self):
        return self.return_value


class Request(_Request):

    @classmethod
    def get(cls):
        return RequestTask()

    @classmethod
    def set(cls, value):
        task = RequestTask()
        task.return_value = value
        return task

