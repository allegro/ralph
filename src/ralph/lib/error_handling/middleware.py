import logging
import traceback

from django.conf import settings
from django.db import OperationalError

from ralph.lib.error_handling.exceptions import WrappedOperationalError


logger = logging.getLogger(__name__)


class OperationalErrorHandlerMiddleware:
    def process_exception(self, request, exception):
        if exception:
            if isinstance(exception, OperationalError):
                logger.error("OperationalError occured. URI: %s, "
                             "user: %s, exception: %s, "
                             "django running since: %s",
                             request.build_absolute_uri(), request.user,
                             exception, settings.START_TIMESTAMP,
                             exc_info=True, stack_info=True)
            elif isinstance(exception, WrappedOperationalError):
                inner_exc = exception.__context__
                logger.error("WrappedOperationalError occured. URI: %s, "
                             "user: %s, SQL query: %s, "
                             "model object: %s, inner exception traceback: %s, "
                             "django running since: %s",
                             request.build_absolute_uri(), request.user,
                             exception.query, exception.model.__dict__,
                             traceback.format_tb(inner_exc.__traceback__),
                             settings.START_TIMESTAMP,
                             exc_info=True, stack_info=True)
        return None
