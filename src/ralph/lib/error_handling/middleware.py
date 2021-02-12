import logging
import traceback

from django.db import OperationalError

from ralph.lib.error_handling.exceptions import WrappedOperationalError


logger = logging.getLogger(__name__)


class OperationalErrorHandlerMiddleware:
    def process_exception(self, request, exception):
        if exception:
            if isinstance(exception, OperationalError):
                logger.error("OperationalError occured. URI: %s, "
                             "user: %s, exception: %s",
                             request.build_absolute_uri(), request.user,
                             exception, exc_info=True, stack_info=True)
            elif isinstance(exception, WrappedOperationalError):
                inner_exc = exception.__context__
                logger.error("WrappedOperationalError occured. URI: %s, "
                             "user: %s, SQL query: %s, "
                             "model object: %s, inner exception traceback: %s",
                             request.build_absolute_uri(), request.user,
                             exception.query, exception.model.__dict__,
                             traceback.format_tb(inner_exc.__traceback__),
                             exc_info=True, stack_info=True)
        return None
