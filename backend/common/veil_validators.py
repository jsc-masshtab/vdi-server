# -*- coding: utf-8 -*-
from common.veil_errors import ValidationError, SimpleError


class MutationValidation:
    """Ищет валидаторы вида validation_argument_field_name.
       На вопрос почему так - не нашел какого-то готового решения для наших реалий."""

    @classmethod
    async def validate_agruments(cls, **kwargs):
        # TODO: сделать аналогичный декоратор?
        for argument in cls.Arguments.__dict__:
            if argument.startswith('_'):
                continue
            field_validation_method_name = 'validate_{}'.format(argument)
            validator = getattr(cls, field_validation_method_name, None)
            if callable(validator):
                try:
                    value = kwargs.get(argument)
                    # Запускаем валидацию только если пришло значение. Обязательность значений указывается в схеме
                    if value:
                        await validator(kwargs, value)
                except ValidationError as E:
                    raise SimpleError('Field \"{}\" - {}'.format(argument, E))
