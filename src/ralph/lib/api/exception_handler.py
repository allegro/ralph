from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def validation_error_exception_handler(exc, context):
    """
    Handle Django ValidationError as an accepted exception,
    There are 2 ValidationErrors, problem occurs
    when using same validator in form and API e.g. MACAddressField
    """

    if isinstance(exc, ValidationError):
        exc = DRFValidationError(str(exc))

    return drf_exception_handler(exc, context)
