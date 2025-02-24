# -*- coding: utf-8 -*-
import json
import sys

from django.core.serializers.base import DeserializationError
from django.core.serializers.json import Serializer as JSONSerializer
from django.utils import six
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from djmoney.utils import get_currency_field_name

from ralph.settings import DEFAULT_CURRENCY_CODE

Serializer = JSONSerializer


def Deserializer(stream_or_string, **options):  # noqa
    """
    Deserialize a stream or string of JSON data.
    """
    # Copied almost without changes from djmoney.serializers (django-money).
    # Adding support for situation where old models to be deserialized have
    # price field, but not price_currency field.
    # In Ralph, price field existed before in various models as
    # a Decimal field. All price fields were migrated to MoneyField
    # without changing the original field name. This can cause problems
    # in original django-money's implementation of Deserializer.
    # This updated Deserializer is needed to get reversion (django-reversion)
    # to work in circumstances described above.

    from django.core.serializers.python import Deserializer as PythonDeserializer
    from django.core.serializers.python import _get_model

    ignore = options.pop("ignorenonexistent", False)

    if not isinstance(stream_or_string, (bytes, six.string_types)):
        stream_or_string = stream_or_string.read()
    if isinstance(stream_or_string, bytes):
        stream_or_string = stream_or_string.decode("utf-8")
    try:
        for obj in json.loads(stream_or_string):
            try:
                Model = _get_model(obj["model"])
            except DeserializationError:
                if ignore:
                    continue
                else:
                    raise
            money_fields = {}
            fields = {}
            field_names = {field.name for field in Model._meta.get_fields()}
            for (field_name, field_value) in six.iteritems(obj["fields"]):
                if ignore and field_name not in field_names:
                    # skip fields no longer on model
                    continue
                field = Model._meta.get_field(field_name)
                if isinstance(field, MoneyField) and field_value is not None:
                    try:
                        currency = \
                            obj["fields"][get_currency_field_name(field_name)]
                    except KeyError:
                        currency = DEFAULT_CURRENCY_CODE
                    money_fields[field_name] = Money(field_value, currency)
                else:
                    fields[field_name] = field_value
            obj["fields"] = fields

            for inner_obj in PythonDeserializer([obj], **options):
                for field, value in money_fields.items():
                    setattr(inner_obj.object, field, value)
                yield inner_obj
    except (GeneratorExit, DeserializationError):
        raise
    except Exception as exc:
        six.reraise(
            DeserializationError, DeserializationError(exc), sys.exc_info()[2]
        )
