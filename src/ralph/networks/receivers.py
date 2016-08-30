from ralph.dns.dnsaas import DNSaaS


def send_ipaddress_to_dnsaas(instance, created, *args, **kwargs):
    keys = ['address', 'hostname']
    data_to_send = {
        key: {
            'old': instance._previous_state[key],
            'new': instance.__dict__[key]
        }
        for key in keys
    }
    DNSaaS().send_ipaddress_data(data_to_send)
