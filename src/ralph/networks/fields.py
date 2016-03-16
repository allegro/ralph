import ipaddress

from django.core.exceptions import ValidationError
from django.db.models.fields import CharField, Field


def network_validator(value):
    """Validator for CIDR notaion."""
    try:
        ipaddress.ip_network(value, strict=False)
    except ipaddress.NetmaskValueError as exc:
        raise ValidationError(exc.message)


class IPNetwork(Field):
    """Field for network with CIDR notation."""

    def __init__(self, *args, **kwargs):
        self.default_validators = [network_validator]
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return CharField(max_length=44).db_type(connection)

    def to_python(self, value):
        if isinstance(value, ipaddress.IPv4Network):
            return value
        if value is None:
            return value
        return ipaddress.ip_network(value)

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return ipaddress.ip_network(value)

    def get_db_prep_save(self, value, connection, **kwargs):
        return str(value)
