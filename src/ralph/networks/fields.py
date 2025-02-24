import ipaddress

from django.core.exceptions import ValidationError
from django.db.models.fields import CharField

MAX_NETWORK_ADDRESS_LENGTH = 44


def network_validator(value):
    """Validator for CIDR notaion."""
    try:
        ipaddress.ip_network(value, strict=False)
    except ipaddress.NetmaskValueError as exc:
        raise ValidationError(exc.message)


class IPNetwork(CharField):
    """Field for network with CIDR notation."""

    def __init__(self, *args, **kwargs):
        self.default_validators = [network_validator]
        kwargs["max_length"] = MAX_NETWORK_ADDRESS_LENGTH
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return CharField(max_length=MAX_NETWORK_ADDRESS_LENGTH).db_type(connection)

    def from_db_value(self, value, expression, connection, *_, **__):
        if value is None:
            return value
        return ipaddress.ip_network(value)

    def get_db_prep_save(self, value, connection, **kwargs):
        return str(value)

    def get_db_prep_value(self, value, connection, **kwargs):
        return str(value)
