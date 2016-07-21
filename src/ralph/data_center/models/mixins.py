from ralph.networks.models import IPAddress


class WithManagementIPMixin(object):
    def _get_management_ip(self):
        eth = self.ethernet_set.select_related('ipaddress').filter(
            ipaddress__is_management=True
        ).first()
        if eth:
            return eth.ipaddress
        return None

    def _get_or_create_management_ip(self):
        ip = self._get_management_ip()
        if not ip:
            eth = self.ethernet_set.create()
            ip = IPAddress(ethernet=eth, is_management=True)
        return ip

    @property
    def management_ip(self):
        ip = self._get_management_ip()
        if ip:
            return ip.address
        return ''

    @management_ip.setter
    def management_ip(self, value):
        ip = self._get_or_create_management_ip()
        ip.address = value
        ip.save()

    @management_ip.deleter
    def management_ip(self):
        ip = self._get_management_ip()
        if ip:
            ip.delete()
            ip.ethernet.delete()

    @property
    def management_hostname(self):
        ip = self._get_management_ip()
        if ip:
            return ip.hostname or ''
        return ''

    @management_hostname.setter
    def management_hostname(self, value):
        ip = self._get_or_create_management_ip()
        ip.hostname = value
        ip.save()
