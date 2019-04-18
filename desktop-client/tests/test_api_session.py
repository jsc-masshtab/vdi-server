

from pytest import fixture

from vdi_thin.services.api_session import ApiSession
from vdi_thin.commands.load_vms import LoadVms


@fixture
def api_session():
    return ApiSession("admin", "veilveil", "http://127.0.0.1:8000")

def test(api_session):
    api_session.init_session()
    api_session.refresh_session_token()