# -*- coding: utf-8 -*-
from graphene.types.structures import NonNull
from common.veil.veil_errors import ValidationError

from common.languages import lang_init


_ = lang_init()


class MutationValidation:
    """Ищет валидаторы вида validation_argument_field_name.
       На вопрос почему так - не нашел какого-то готового решения для наших реалий."""

    @classmethod
    async def validate(cls, **kwargs):
        # TODO: сделать аналогичный декоратор?
        for argument_name in cls.Arguments.__dict__:
            if argument_name.startswith("_"):
                continue
            field_validation_method_name = "validate_{}".format(argument_name)
            validator = getattr(cls, field_validation_method_name, None)
            argument = getattr(cls.Arguments, argument_name)

            if callable(validator):
                try:
                    value = kwargs.get(argument_name)
                    # Проверка NonNull разрешает пустой список. Хочется иметь возможность ограничить такое валидатором.
                    if value is not None or isinstance(argument, NonNull):
                        await validator(kwargs, value)
                except ValidationError as E:
                    msg = _('Field "{}" - {}.').format(argument_name, E)
                    raise ValidationError(msg.replace("..", "."))
