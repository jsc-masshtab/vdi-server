import pytest

from starlette.testclient import TestClient

from vdi.application.app import app


@pytest.mark.ws
def test_resources_subscriptions():
    client = TestClient(app)
    with client.websocket_connect('/subscriptions') as websocket:
        # subscribe
        websocket.send_text('add /domains/')
        data = websocket.receive_json()
        print('data_from_server: ', data)
        assert not data['error']

        # unsubscribe
        websocket.send_text('delete /domains/')
        data = websocket.receive_json()
        print('data_from_server: ', data)
        assert not data['error']
