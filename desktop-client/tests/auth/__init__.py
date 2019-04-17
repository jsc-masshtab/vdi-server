
from unittest.mock import MagicMock
from pytest import fixture

from vdi_thin.app import Application
from vdi_thin.services.api_session import ApiSession
from vdi_thin.commands.login import LoginCommand

@fixture
def app():
    return Application()

@fixture
def api_session(app):
    api_session = ApiSession("admin", "veilveil", "http://127.0.0.1:8000")
    app.api_session = api_session
    return api_session


@fixture
def login_cmd(app, api_session):
    return LoginCommand(
            app, api_session=api_session,
            login_handler=MagicMock())
