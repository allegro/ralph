import json
from collections import defaultdict

from django.core import serializers


def obj_to_dict(model_instance, fields=None):
    if not model_instance:
        return {}
    serial_obj = serializers.serialize(
        'json', [model_instance], fields=fields
    )
    obj_as_dict = json.loads(serial_obj)[0]['fields']
    obj_as_dict['pk'] = model_instance.pk
    return defaultdict(str, obj_as_dict)
