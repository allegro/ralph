import pkg_resources

from django.conf import settings
from django.utils import lru_cache


@lru_cache.lru_cache(maxsize=None)
def get_hook(module_name, name, variant=None):
    loaded_func = None
    full_name = '.'.join([module_name, name])

    if variant is None:
        variant = settings.ENTRY_POINTS_CONFIGURATION[full_name]
    for entry_point in pkg_resources.iter_entry_points(full_name):
        if variant == entry_point.name:
            loaded_func = entry_point.load()
            break
    if loaded_func is None:
        raise ValueError("Entry point {} doesn't exist".format(full_name))
    return loaded_func

