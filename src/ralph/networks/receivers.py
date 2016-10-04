from ralph.dns.dnsaas import DNSaaS
from ralph.virtual.models import CloudHost


def update_dns_record(instance, created, *args, **kwargs):
    if isinstance(instance.ethernet.base_object, CloudHost):
        return
    keys = ['address', 'hostname']
    data_to_send = {
        'old': {
            key: instance._previous_state[key] for key in keys
        },
        'new': {
            key: instance.__dict__[key] for key in keys
        }
    }
    data_to_send['action'] = 'add' if created else 'update'
    if data_to_send['old']['hostname'] is not None:
        DNSaaS().send_ipaddress_data(data_to_send)


def delete_dns_record(instance, *args, **kwargs):
    if isinstance(instance.ethernet.base_object, CloudHost):
        return
    DNSaaS().send_ipaddress_data({
        'address': instance.address,
        'hostname': instance.hostname,
        'action': 'delete'
    })
