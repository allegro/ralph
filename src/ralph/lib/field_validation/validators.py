from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _


class HostnameValidator(RegexValidator):
    regex = r'^[a-zA-Z0-9.-]+$'
    message = _('Hostname can contain only alphabetical characters (A-Z), '
                'numeric characters (0-9), the minus sign (-), and the period (.)')
    code = 'invalid_hostname'

    def __call__(self, value):
        super().__call__(value)
