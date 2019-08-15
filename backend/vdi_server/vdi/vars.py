
from cached_property import cached_property as cached
from classy_async import Task



class JWTUser(Task):

    @classmethod
    def set(cls, value):
        obj = cls()
        obj.value = value
        return obj

    async def run(self):
        return self.value
