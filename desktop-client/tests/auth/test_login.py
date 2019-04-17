


from . import *

def test_execute(login_cmd, app):
    login_cmd.run()
    # app.api_session.init_session()
    url = 'http://127.0.0.1:8000/'
    r = app.api_session.get(url)
    print(r)