from typing import Any, Callable, Optional

import pkg_resources
from django.conf import settings
from django.utils import lru_cache


def hook_name_to_env_name(name, prefix='HOOKS'):
    """
    >>> hook_name_to_env_name('foo.bar_baz')
    HOOKS_FOO_BAR_BAZ
    >>> hook_name_to_env_name('foo.bar_baz', 'PREFIX')
    PREFIX_FOO_BAR_BAZ
    """
    return '_'.join([prefix, name.upper().replace('.', '_')])


@lru_cache.lru_cache(maxsize=None)
def get_hook(name: str, variant: Optional[str] = None) -> Callable[..., Any]:
    """Returns function based on configuration and entry_points."""
    loaded_func = None

    if variant is None:
        variant = settings.HOOKS_CONFIGURATION[name]

    for entry_point in pkg_resources.iter_entry_points(name):
        if variant == entry_point.name:
            loaded_func = entry_point.load()
            break
    else:
        raise ValueError("Entry point {} doesn't exist".format(name))
    return loaded_func
