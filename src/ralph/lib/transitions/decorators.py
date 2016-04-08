# -*- coding: utf-8 -*-
from functools import wraps

from ralph.lib.transitions.conf import TRANSITION_ATTR_TAG


def transition_action(method=None, **kwargs):
    def decorator(func):
        func.verbose_name = kwargs.get(
            'verbose_name', func.__name__.replace('_', ' ').capitalize()
        )
        func.return_attachment = kwargs.get('return_attachment', False)
        func.form_fields = kwargs.get('form_fields', {})
        func.run_after = kwargs.get('run_after', [])
        func.help_text = kwargs.get('help_text', '')
        func.precondition = kwargs.get('precondition', lambda instances: {})
        func.disable_save_object = kwargs.get('disable_save_object', False)
        func.only_one_action = kwargs.get('only_one_action', False)
        func.is_async = kwargs.get('is_async', False)
        setattr(func, TRANSITION_ATTR_TAG, True)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if 'model' in kwargs:
            setattr(kwargs['model'], func.__name__, wrapper)

            from django.contrib.contenttypes.models import ContentType
            from ralph.lib.transitions.models import Action
            action, _ = Action.objects.get_or_create(name=func.__name__)
            content_type = ContentType.objects.get_for_model(kwargs['model'])
            action.content_type.add(content_type)

        return wrapper

    if callable(method):
        return decorator(method)
    return decorator
