from __future__ import annotations

import functools
import inspect
import json
import logging
from pathlib import Path
from typing import get_type_hints

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def file_cache(subdir: str, key_arg: str | None = None):
    """
    NOT PROD READY

    Filesystem cache decorator for functions returning Pydantic models or JSON-serializable data.
    Cache invalidation must be handled manually by deleting the cache files.

    Uses settings.FILE_CACHE_DIR as the base directory. If FILE_CACHE_DIR is not set,
    caching is disabled and the function is called directly.

    Args:
        subdir: subdirectory under FILE_CACHE_DIR for this function's cache files.
        key_arg: name of the argument to use as cache key filename.
                 If not specified, uses the first argument (skipping 'self'/'cls').

    Usage:
        @file_cache("get_switchports")
        def get_switchports(self, switch_hostname: str) -> SwitchDTO:
            ...
    """

    def decorator(func):
        # Determine which argument to use as key
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        if key_arg:
            _key_arg = key_arg
        else:
            # Skip self/cls
            non_self_params = [p for p in params if p not in ("self", "cls")]
            _key_arg = non_self_params[0] if non_self_params else None

        # Determine return type for deserialization
        hints = get_type_hints(func)
        return_type = hints.get("return")

        is_pydantic = (
            return_type and isinstance(return_type, type) and issubclass(return_type, BaseModel)
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from django.conf import settings

            # Reserved kwarg to bypass a stale cache entry: skip the read and
            # overwrite the cache with a freshly computed value. Never forwarded
            # to the wrapped function.
            force_refresh = kwargs.pop("force_refresh", False)

            cache_base = getattr(settings, "FILE_CACHE_DIR", None)
            if not cache_base:
                return func(*args, **kwargs)

            cache_dir = Path(cache_base) / subdir

            if _key_arg:
                # Keyed cache: one file per key value
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                key_value = bound.arguments[_key_arg]
                cache_file = cache_dir / f"{key_value}.json"
            else:
                # No-arg cache: single file for the whole function
                cache_file = cache_dir / "_result.json"

            if cache_file.exists() and not force_refresh:
                logger.info("file_cache hit: %s", cache_file)
                content = cache_file.read_text()
                if is_pydantic:
                    return return_type.model_validate_json(content)
                else:
                    return json.loads(content)

            result = func(*args, **kwargs)

            cache_dir.mkdir(parents=True, exist_ok=True)
            if is_pydantic:
                cache_file.write_text(result.model_dump_json(indent=2))
            else:
                cache_file.write_text(json.dumps(result, indent=2, default=str))
            logger.info("file_cache store: %s", cache_file)

            return result

        return wrapper

    return decorator
