import graphene

from graphql.language.ast import StringValue

import six


class ShortString(graphene.Scalar):
    """The scalar type represents textual data, represented as UTF-8 character sequences, with a length of 255."""

    @staticmethod
    def coerce_string(value):
        if isinstance(value, bool):
            return u"true" if value else u"false"
        str_value = six.text_type(value)
        if len(str_value) > 255:
            str_value = str_value[:255]
        return str_value

    serialize = coerce_string
    parse_value = coerce_string

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, StringValue):
            if len(ast.value) > 255:
                ast.value = ast.value[:255]
            return ast.value
