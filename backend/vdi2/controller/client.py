from common.veil_client import VeilHttpClient


class ControllerClient(VeilHttpClient):

    def __init__(self, controller_ip: str):
        super().__init__(controller_ip)

    def check_credentials(self):
        pass
