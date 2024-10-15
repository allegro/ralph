import base64
import json

from dj.choices.fields import ChoiceField
from django.db.models.fields import BooleanField

from ralph.admin.helpers import get_field_by_relation_path


def encode_params(params):
    return base64.urlsafe_b64encode(json.dumps(params).encode())


def decode_params(value):
    if not value:
        return {}
    return json.loads(base64.urlsafe_b64decode(value).decode())


def normalize_value(model_class, label, value):
    """Convert value to Python's type based on value."""
    field = get_field_by_relation_path(model_class, label)
    if isinstance(field, ChoiceField):
        choices = field.choice_class()
        try:
            value = [i[0] for i in choices if i[1] == value].pop()
        except IndexError:
            # NOTE(romcheg): Choice not found for the filter value.
            #                Leaving it as is.
            pass
    elif isinstance(field, BooleanField):
        value = field.to_python(value)
    return value
