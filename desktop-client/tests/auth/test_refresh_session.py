
from . import *

def test_execute(login_cmd, app):
    login_cmd.run()
    app.api_session.init_session()
    app.api_session.refresh_session_token()