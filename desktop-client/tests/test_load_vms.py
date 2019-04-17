

from pytest import fixture

from vdi_thin.services.api_session import ApiSession
from vdi_thin.commands.load_vms import LoadVms

@fixture
def app():
    return None

@fixture
def api_session():
    return ApiSession("admin", "veilveil", "http://127.0.0.1:8000")

@fixture
def cmd(app, api_session):
    on_vm_load_finish = lambda *args: None
    return LoadVms(app, api_session=api_session, on_finish=on_vm_load_finish)

def test_execute(cmd):
    cmd.run()