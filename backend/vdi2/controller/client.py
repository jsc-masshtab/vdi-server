from common.veil_client import VeilHttpClient



class ControllerClient(VeilHttpClient):

    def __init__(self, controller_ip: str):
        super().__init__(controller_ip)

    async def fetch_version(self):
        """check if controller accesseble"""
        url = self.api_url + 'controllers/base-version/'
        response = await self.fetch_with_response(url=url, method='GET')
        return response.get('version')
