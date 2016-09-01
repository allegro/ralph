from ralph.dns.dnsaas import DNSaaS


def update_dns_record(instance, created, *args, **kwargs):
    keys = ['address', 'hostname']
    data_to_send = {
        key: instance.__dict__[key]
        for key in keys
    }
    data_to_send['action'] = 'add' if created else 'update'
    data_to_send['ip'] = instance._previous_state['address']
    DNSaaS().send_ipaddress_data(data_to_send)


def delete_dns_record(instance, *args, **kwargs):
    DNSaaS().send_ipaddress_data({
        'ip': instance.address,
        'action': 'delete'
    })
