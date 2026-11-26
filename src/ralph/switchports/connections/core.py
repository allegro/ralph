from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from ralph.switchports.models import Port


def connected_to(port: Port) -> Port | None:
    if conn := getattr(port, "connectionmember", None):
        try:
            return conn.connection.members.exclude(port=port).get().port
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return None
    return None
