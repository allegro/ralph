from django.contrib.contenttypes.models import ContentType

from ralph.dns.dnsaas import DNSaaS
from ralph.virtual.models import CloudHost

INVALID_MODELS = [CloudHost]


def _should_send_dnsaas_request(ip_instance):
    """
    Return True if update/delete info should be sent to DNSaaS.

    Data should be sent if IP address has base object assigned (through
    Ethernet) and it's not CloudHost.
    """
    eth = ip_instance.ethernet
    invalid_content_types = ContentType.objects.get_for_models(*INVALID_MODELS).values()
    return eth and eth.base_object.content_type not in invalid_content_types


def _get_connected_service_uid(ip_instance):
    """
    Return connected with base object (through Ethernet) service UID or None if
    IP address has not ethernet.
    """

    eth = ip_instance.ethernet
    if eth:
        service = eth.base_object.service
        if service:
            return service.uid


def update_dns_record(instance, created, *args, **kwargs):
    if not _should_send_dnsaas_request(instance):
        return
    keys = ["address", "hostname"]
    old = {key: instance._previous_state[key] for key in keys}
    new = {key: instance.__dict__[key] for key in keys}
    if old != new and old["hostname"] is not None:
        data_to_send = {
            "old": old,
            "new": new,
            "service_uid": _get_connected_service_uid(instance),
            "action": "add" if created else "update",
        }
        DNSaaS().send_ipaddress_data(data_to_send)


def delete_dns_record(instance, *args, **kwargs):
    if not _should_send_dnsaas_request(instance):
        return
    DNSaaS().send_ipaddress_data(
        {"address": instance.address, "hostname": instance.hostname, "action": "delete"}
    )
