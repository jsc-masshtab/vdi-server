from common.veil_client import VeilHttpClient


class ControllerClient(VeilHttpClient):

    def __init__(self, controller_ip: str):
        super().__init__(controller_ip)

    async def fetch_version(self):
        """check if controller accesseble"""
        url = self.based_url + '/controllers/base-version/'
        await self.fetch(url=url, method='GET')
