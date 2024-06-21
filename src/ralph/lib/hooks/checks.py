import enum

import pkg_resources
from django.conf import settings
from django.core.checks import Error

from ralph.lib.hooks import hook_name_to_env_name


class Codes(enum.Enum):
    IMPORT_ERROR = 1
    EMPTY_ENTRY_POINT = 2
    INVALID_ENV_VAR = 3


ERRORS = {
    Codes.IMPORT_ERROR: lambda key: Error(
        "Somethings goes wrong during import entry point ({})".format(key),  # noqa
        hint="Check function and value of entry point.",
        id="hooks.E001"
    ),
    Codes.EMPTY_ENTRY_POINT: lambda key: Error(
        "Entry point \"{}\" is not defined in any installed package!".format(key), # noqa
        hint="Add entry point to setup.py and add default value to them.",
        id="hooks.E002"
    ),
    Codes.INVALID_ENV_VAR: lambda key, active_variant, variants: Error(
        "The environment variable {}={} is not valid (incorrect value).".format(  # noqa
            hook_name_to_env_name(key), active_variant
        ),
        hint="Consider one of these values: {}".format(
            ', '.join(variants)
        ),
        id="hooks.E002"
    )
}


def check_configuration(**kwargs):
    errors = []
    for key, active_variant in settings.HOOKS_CONFIGURATION.items():
        variants = []
        found = False
        ep = None
        for ep in pkg_resources.iter_entry_points(key):
            variants.append(ep.name)
            try:
                ep.load()
            except ImportError:
                errors.append(ERRORS[Codes.IMPORT_ERROR](key))
            if active_variant == ep.name:
                found = True

        if ep is None:
            errors.append(ERRORS[Codes.EMPTY_ENTRY_POINT](key))
            break

        if not found:
            errors.append(
                ERRORS[Codes.INVALID_ENV_VAR](key, active_variant, variants)
            )

    return errors
