# -*- coding: utf-8 -*-
from cached_property import cached_property
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from tornado.escape import json_decode

from settings import VEIL_REQUEST_TIMEOUT, VEIL_CONNECTION_TIMEOUT, VEIL_MAX_BODY_SIZE, VEIL_MAX_CLIENTS
from common.veil_errors import NotFound, Unauthorized, ServerError, Forbidden, ControllerNotAccessible, BadRequest
from common.veil_errors import ValidationError, MeaningError
from common.veil_decorators import prepare_body

from languages import lang_init
from journal.journal import Log as log


_ = lang_init()

# TODO: в 2.1 планируем отказаться от текущей реализации
# TODO: добавить обработку исключений
# TODO: нужно менять статус контроллера и прочих сущностей после нескольких неудачных попыток подключения
# TODO: нужно возвращать контроллеры только в определенном статусе.
# TODO: нужно завершать выполнение сущностей клиента и т.п. при изменении статуса сущности (отвалился контроллер).
# TODO: после окончания переноса кода и написания базовых тестов - протестировать замену property на cached_property

# TODO: убрать переводы для переменных отправляемых на Veil
# TODO: кеширование ресурсов

AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient",
                          max_clients=VEIL_MAX_CLIENTS,
                          max_body_size=VEIL_MAX_BODY_SIZE)


class VeilHttpClient:
    """Abstract class for Veil ECP connection. Simply non-blocking HTTP(s) fetcher from remote Controller.
       response_types always json"""

    def __init__(self, controller_ip: str, token: str = None):
        """Use create instead of init."""
        self._client = AsyncHTTPClient()
        self.controller_ip = controller_ip
        self.token = token

    @cached_property
    def api_url(self):
        return 'http://{}/api/'.format(self.controller_ip)

    @property
    async def headers(self):
        """controller ip-address must be set in the descendant class."""
        headers = {
            'Authorization': _('jwt {}').format(self.token),
            'Content-Type': 'application/json',
            'User-Agent': 'VeiL-api-client/1.0 VDI/2.0',
            'Accept-Language': 'en',
            'Cache-Control': 'max-age=0',
            'Accept-Charset': 'utf-8',
            'Connection': 'close'
        }
        return headers

    @staticmethod
    def parse_veil_errors(url, body):
        """Извлекает ошибки из ответа veil."""
        if isinstance(body, dict):
            errors = body.get('errors')
            if isinstance(errors, list):
                # VeiL 4.3
                detail = ';'.join([error['detail'] for error in errors if error.get('detail')])
            elif isinstance(errors, dict):
                # VeiL 4.2
                detail = errors.get('detail')
            elif errors is None:
                detail = ';'.join([error[0] if isinstance(error, list) else error for error in body.values()])
            else:
                # WtF
                detail = None
        elif isinstance(body, str):
            detail = body
        else:
            detail = ''
        if detail:
            verbose_detail = '{}: {}'.format(url, detail)
        else:
            verbose_detail = url
        log.debug(verbose_detail)
        # т.к. message в Event огрничен 256 символами
        return verbose_detail[:256]

    async def controller_version(self):
        """Возвращает строку с версией контроллера"""
        from controller.models import Controller
        version = await Controller.get_controller_version_by_address(self.controller_ip)
        major_version, minor_version, patch_version = version.split('.')
        return major_version, minor_version

    @prepare_body
    async def fetch(self, url: str, method: str, headers: dict = None, body: str = '', controller_control: bool = True):
        """

        :param url: URL запроса
        :param method: Метод запроса
        :param headers: Заголовки запроса
        :param body: Тело запроса
        :param controller_control: нужно ли управлять контроллером по результатам исключения
        :return: HttpResponse
        """
        if not headers:
            headers = await self.headers
        request = HTTPRequest(url=url,
                              method=method,
                              headers=headers,
                              body=body,
                              connect_timeout=VEIL_CONNECTION_TIMEOUT,
                              request_timeout=VEIL_REQUEST_TIMEOUT)

        try:
            response = await self._client.fetch(request)
        except HTTPClientError as http_error:
            body = self.get_response_body(http_error.response)
            detail = self.parse_veil_errors(url, body)

            log.debug(detail)

            if controller_control:
                from resources_monitoring.resources_monitor_manager import resources_monitor_manager
                await resources_monitor_manager.remove_controller(self.controller_ip)

            if http_error.code == 400:
                raise BadRequest(body)
            elif http_error.code == 401:
                raise Unauthorized(_('Controller {} connection error.').format(self.controller_ip))
            elif http_error.code == 403:
                raise Forbidden(body)
            elif http_error.code == 404:
                raise NotFound(_('Fail to fetch resource from ECP.'), url)
            elif http_error.code == 408:
                raise ControllerNotAccessible(body)
            elif http_error.code == 500:
                raise ServerError(body)
            elif http_error.code == 599:
                raise ServerError(str(http_error))
        return response

    @staticmethod
    def get_response_body(response):
        if not response:
            return

        response_headers = response.headers
        response_content_type = response_headers.get('Content-Type')

        # log.debug('Response headers: {}'.format(response_headers))

        if not isinstance(response_content_type, str):
            raise ValidationError(_('Can\'t process Content-Type.'))

        if response_content_type.lower().find('json') == -1:
            log.debug('Unexpected response content-type.')
            return dict()
        try:
            response = json_decode(response.body)
        except ValueError as E:
            raise MeaningError(E)
            response = dict()
        return response

    async def fetch_with_response(self, url: str, method: str, headers: dict = None, body: str = None,
                                  controller_control: bool = True):
        """Check response headers. Search json in content-type value"""
        # print('fetch_with_response: url {} method {} headers {} '.format(url, method, headers))
        response = await self.fetch(url=url, method=method, headers=headers, body=body,
                                    controller_control=controller_control)
        response_body = self.get_response_body(response)
        return response_body

    async def check_task_status(self, task_id):
        """Проверяет статус выполнения задачи на контроллере"""
        endpoint_url = '{api_url}tasks/{task_id}/'.format(api_url=self.api_url, task_id=task_id)
        response = await self.fetch_with_response(url=endpoint_url, method='GET')
        if response.get('status') == 'SUCCESS':
            return True
        return False
