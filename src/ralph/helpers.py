import logging
import pickle
from functools import wraps

from django.conf import settings
from django.core.cache import caches, DEFAULT_CACHE_ALIAS
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def add_request_to_form(form_class, request):
    form_class._request = request
    return form_class


def get_model_view_url_name(model, view_name, with_admin_namespace=True):
    """
    Return url name for model additional view (site). Example:
    >>> get_model_view_url_name(DataCenterAsset, 'attachment')
    'admin:data_center_datacenterasset_attachment'
    """
    params = model._meta.app_label, model._meta.model_name
    url = "{}_{}_{view_name}".format(*params, view_name=view_name)
    if with_admin_namespace:
        url = "admin:" + url
    return url


def generate_pdf_response(pdf_data, file_name):
    """
    Return file response for pdf file with provided content and file name
    after download.
    """
    # TODO: unify with attachments
    response = HttpResponse(
        content=pdf_data,
        content_type="application/pdf",
    )
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(
        file_name,
    )
    return response


CACHE_DEFAULT = object()


def _cache_key_hash(func, *args, **kwargs):
    return pickle.dumps((func.__module__, func.__name__, args, kwargs))


def cache(seconds=300, cache_name=DEFAULT_CACHE_ALIAS, skip_first=False):
    """
    Cache the result of a function call with particular parameters for specified
    number of seconds.

    Args:
        * skip_first - set to True if first argument should not be considered
          when calculating hash of arguments (useful when first argument
          is instance of a class (self)).
    """

    def _cache(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_proxy = caches[cache_name]
            key = _cache_key_hash(func, *(args[1:] if skip_first else args), **kwargs)
            result = cache_proxy.get(key, default=CACHE_DEFAULT)
            if result is CACHE_DEFAULT:
                logger.debug("Recalculating result of {}".format(func.__name__))
                result = func(*args, **kwargs)
                cache_proxy.set(key, result, seconds)
            else:
                logger.debug("Taking result of {} from cache".format(func.__name__))
            return result

        if settings.USE_CACHE:
            return wrapper
        else:
            return func

    return _cache
