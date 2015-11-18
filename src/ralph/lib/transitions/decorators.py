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
        setattr(func, TRANSITION_ATTR_TAG, True)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    if callable(method):
        return decorator(method)
    return decorator
