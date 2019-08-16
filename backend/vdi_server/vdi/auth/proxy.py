import json
from vdi.tasks.client import HttpClient
from vdi.settings import settings

from vdi.app import Request


async def fetch_token(username, password):
    request = await Request.get()
    host, _ = request.scope['server']
    port = settings.auth_server['port']
    scheme = request.scope['scheme']
    auth_url = f'{scheme}://{host}:{port}/auth'
    http_client = HttpClient()
    body = json.dumps({'username': username, 'password': password})
    return await http_client.fetch(auth_url, method='POST', body=body)