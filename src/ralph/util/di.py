# -*- coding: utf-8 -*-
"""Tools for dependency injection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pkg_resources import iter_entry_points


def is_extra_available(name):
    """Checks if extra data is provided.

    :param name: The name of the extra data.

    :return: Boolean value
    """
    for _ in iter_entry_points('ralph_extra_data', name=name):
        return True
    return False


def get_extra_data(name, *args, **kwargs):
    """A central function for injecting extra data.

    :param name: The name of the extra data.

    The rest of the params will be passed to the data provider. The first param
    should be conventionally a 'context' e.g. a device, an asset a CI etc.

    :return: The data or None if provider is not present
    """

    handlers = list(iter_entry_points('ralph_extra_data', name=name))
    if not handlers:
        return None
    if len(handlers) > 1:
        raise RuntimeError(
            'Multiple handlers provided for extra_data type {}'.format(name)
        )
    handler = handlers[0].load()
    return handler(*args, **kwargs)
