# -*- coding: utf-8 -*-
import inspect
import logging
import ssl
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib as smtp

from common.languages import _local_
from common.models.event import Event
from common.settings import DEBUG
from common.veil.veil_gino import EntityType


def singleton(cls):
    """Декоратор превращающий класс в классический синглтон."""
    __instances = {}

    def get_instance(*args, **kwargs):
        if cls not in __instances:
            __instances[cls] = cls(*args, **kwargs)
        return __instances[cls]

    return get_instance


def cut_message(func):
    """Декоратор, который обрезает хвост сообщения."""

    def wrapper(self, message, *args, **kwargs):
        message = message[:255]
        return func(self, message, *args, **kwargs)

    return wrapper


def check_debug_message(func):
    """Декоратор, который проверяет режим DEBUG и расширяет сообщения."""

    def wrapper(self, message, *args, **kwargs):
        if self._Log__debug_enabled:
            call_info = self._Log__get_call_info()
            message = " ".join([call_info, message])
        return func(self, message, *args, **kwargs)

    return wrapper


def check_parameters(func):
    """Декоратор, который проверяет входные параметры для ивентов."""

    def wrapper(self, message, entity=None, description=None, *args, **kwargs):
        if not entity:
            entity = {"entity_type": EntityType.SECURITY, "entity_uuid": None}
        if message and not isinstance(message, str):
            message = str(message)
        if description and not isinstance(description, str):
            description = str(description)
        return func(self, message, entity, description, *args, **kwargs)

    return wrapper


@singleton
class Log:
    """Системный журнал.

    Одновременно может существовать только 1 инстанс (для этого декоратор синглтон).
    Все методы асинхронные для универсализации запуска.

    Аргументы:
        log_level: уровень логирования (можно задать аргументом запуска app)
        debug: передастся в propagate
    """

    __TYPE_INFO = 0
    __TYPE_WARNING = 1
    __TYPE_ERROR = 2
    __TYPE_DEBUG = 3

    @staticmethod
    def __get_call_info():
        """Получаем атрибуты функции из которой вызван log.

        индекс стека установлен по принципу наследования (app -> Log -> debug -> __log_debug)
        :return: fn, func, ln
        """
        stack = inspect.stack()
        file_name = stack[3][1]
        line = stack[3][2]
        func = stack[3][3]
        if line and not isinstance(line, str):
            line = str(line)
        # return file_name, func, line
        return " ".join([file_name, func, line])

    @staticmethod
    def __set_propagate(val: bool):
        """Для всех найденных логгеров меняем значение propagate."""
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).propagate = val
        # gino нет в списке логгеров, не стал выяснять почему
        logging.getLogger("gino").propagate = False

    def __init__(self):
        # Set propagate level for inner loggers.
        self.__set_propagate(val=DEBUG)
        # Настраиваем консольный логгер
        root_logger = logging.getLogger()
        # Отключаем все настроенные раннее хендлеры (tornado.options делает преднастроенное безобразие)
        [root_logger.removeHandler(handler) for handler in root_logger.handlers]
        # Настраиваем формат logger`а
        logging.basicConfig(
            # level=LOG_LEVEL, # прокинется из tornado_options
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler(stream=sys.stdout)],
        )
        self.__debug_enabled = DEBUG
        self.__logger = root_logger

    @check_debug_message
    def __log_debug(self, message: str):
        self.__logger.debug(message)

    @check_debug_message
    def __log_info(self, message: str):
        self.__logger.info(message)

    @check_debug_message
    def __log_warning(self, message: str):
        self.__logger.warning(message)

    @check_debug_message
    def __log_error(self, message: str):
        self.__logger.error(message)

    @cut_message
    async def __event(
        self,
        message: str,
        description: str = None,
        user: str = "system",
        entity: dict = None,
        event_type: int = 3
    ):
        await Event.create_event(
            event_type=event_type,
            msg=message,
            description=description,
            user=user,
            entity_dict=entity,
        )

    def _debug(self, message: str):
        """Синхронно запишет сообщение в logging с уровнем DEBUG."""
        if message and not isinstance(message, str):
            message = str(message)
        self.__log_debug(message)

    @check_parameters
    async def debug(
        self,
        message: str,
        entity: dict = None,
        description: str = None,
        user: str = "system",
    ):
        """Запишет сообщение в logging и таблицу Event с уровнем DEBUG."""
        self.__log_debug(message)
        if DEBUG:
            event_type = self.__TYPE_DEBUG
            await self.__event(message, description, user, entity, event_type)

    @check_parameters
    async def info(
        self,
        message: str,
        entity: dict = None,
        description: str = None,
        user: str = "system",
    ):
        """Запишет сообщение в logging и таблицу Event с уровнем INFO."""
        self.__log_info(message)
        event_type = self.__TYPE_INFO
        await self.__event(message, description, user, entity, event_type)
        await send_mail_async(event_type=event_type,
                              subject=_local_("INFO message from VeiL Broker."),
                              message=message,
                              description=description)

    @check_parameters
    async def warning(
        self,
        message: str,
        entity: dict = None,
        description: str = None,
        user: str = "system",
    ):
        """Запишет сообщение в logging и таблицу Event с уровнем WARNING."""
        self.__log_warning(message)
        event_type = self.__TYPE_WARNING
        await self.__event(message, description, user, entity, event_type)
        await send_mail_async(event_type=event_type,
                              subject=_local_("Warning message from VeiL Broker."),
                              message=message,
                              description=description)

    @check_parameters
    async def error(
        self,
        message: str,
        entity: dict = None,
        description: str = None,
        user: str = "system",
    ):
        """Запишет сообщение в logging и таблицу Event с уровнем ERROR."""
        self.__log_error(message)
        event_type = self.__TYPE_ERROR
        await self.__event(message, description, user, entity, event_type)
        await send_mail_async(event_type=event_type,
                              subject=_local_("Error message from VeiL Broker."),
                              message=message,
                              description=description)


async def send_mail_async(event_type, subject, message, description=None, text_type="plain"):
    """Отправляет письмо, если настроен smtp сервер.

    :param event_type: Уровень сообщения.
    :type subject: int

    :param subject: Тема письма.
    :type subject: str

    :param message: Текст сообщения внутри письма
    :type message: str

    :param description: Текст описания внутри письма.
    :type description: str

    :param text_type: Подтип текста Mime, по умолчанию: "plain" (может быть "html").
    :type text_type: str

    """
    from common.models.auth import User
    from common.models.settings import Settings

    smtp_params = await Settings.select("smtp_settings").gino.first()
    # если level 2 - только error, 1 - warning и error, 0 - все, 4 - выключены оповещения. 3 не надо ставить!!!
    if event_type < smtp_params[0]["level"]:
        return

    if not smtp_params[0]["hostname"] and not smtp_params[0]["from_address"]:
        await system_logger.debug(_local_("SMTP server is not configured."))
        return

    emails = await User.select("email").where(
        User.is_superuser & User.is_active).gino.all()

    recipient_emails = list()
    for email in emails:
        if email[0]:
            if len(email[0]) > 1:
                recipient_emails.append(email[0])
    if len(recipient_emails) < 1:
        return

    recipients = ", ".join(recipient_emails)
    text = "Text: {}\n\nDescription: {}".format(message, description)

    try:
        msg = MIMEMultipart()
        msg.add_header("From", smtp_params[0].get("from_address", "veil@mashtab.org"))
        msg.add_header("To", recipients)
        msg.add_header("Subject", subject)
        msg.attach(MIMEText(text, text_type, "utf-8"))

        hostname = smtp_params[0].get("hostname", "localhost")
        is_ssl = smtp_params[0].get("SSL", False)
        is_tls = smtp_params[0].get("TLS", False)
        port = smtp_params[0].get("port", 465 if is_ssl else 25)
        server = smtp.SMTP(hostname=hostname, port=port, use_tls=is_ssl)
        await server.connect()

        # нужно, т.к. вылезает ошибка: "ssl.CertificateError: hostname '192.168.10.7' doesn't match 'mail.mashtab.org'"
        ssl.match_hostname = lambda cert, hostname: True
        if is_tls:
            await server.starttls()
        else:
            await server.ehlo()
        if "user" in smtp_params[0]:
            await server.login(smtp_params[0]["user"], smtp_params[0]["password"])
        await server.send_message(msg)
        await server.quit()
        return True
    except (smtp.SMTPException, smtp.SMTPConnectError, ValueError) as e:
        error_msg = _local_("Error in smtp server: {}.".format(e))
        await system_logger.debug(error_msg)
        return False

system_logger = Log()
