from ralph.dns.dnsaas import DNSaaS


def update_dns_record(instance, created, *args, **kwargs):
    keys = ['address', 'hostname']
    data_to_send = {
        'new': {
            key: instance.__dict__[key] for key in keys
        },
        'old': {
            key: instance._previous_state[key] for key in keys
        }
    }
    data_to_send['action'] = 'add' if created else 'update'
    DNSaaS().send_ipaddress_data(data_to_send)


def delete_dns_record(instance, *args, **kwargs):
    DNSaaS().send_ipaddress_data({
        'address': instance.address,
        'hostname': instance.hostname,
        'action': 'delete'
    })
