import logging
import traceback

from django.conf import settings
from django.db import OperationalError

from ralph.lib.error_handling.exceptions import WrappedOperationalError


logger = logging.getLogger(__name__)


class OperationalErrorHandlerMiddleware:
    def process_exception(self, request, exception):
        if exception:
            request_id = request.META.get('HTTP_X_REQUEST_ID', '-')
            if isinstance(exception, OperationalError):
                logger.error("OperationalError occured. URI: %s, "
                             "user: %s, exception: %s, "
                             "django running since: %s, "
                             "request id: %s",
                             request.build_absolute_uri(), request.user,
                             exception, settings.START_TIMESTAMP,
                             request_id,
                             exc_info=True, stack_info=True,
                             extra={'request_id': request_id}
                             )
                raise exception
            elif isinstance(exception, WrappedOperationalError):
                inner_exc = exception.__context__
                logger.error("WrappedOperationalError occured. URI: %s, "
                             "user: %s, SQL query: %s, "
                             "model object: %s, original_error: %s, "
                             "inner exception traceback: %s, "
                             "django running since: %s, "
                             "request id: %s",
                             request.build_absolute_uri(), request.user,
                             str(exception.query), exception.model.__dict__,
                             exception.original_error_str,
                             traceback.format_tb(inner_exc.__traceback__),
                             settings.START_TIMESTAMP, request_id,
                             exc_info=True, stack_info=True,
                             extra={'request_id': request_id}
                             )
                raise inner_exc
        return None
