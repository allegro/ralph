from django.core.exceptions import ValidationError

from ralph.networks.models import IPAddress


class WithManagementIPMixin(object):
    """
    This mixin helps to handle management_ip and hostname (ex. for
    DataCenterAsset and Cluster).

    What happen when management ip is assigned:
    * first, existing management ip for this host is fetched
    * if there is change in address value, existing management ip (IPAddress)
      is removed (unless it's reserved IP - then it's detached from current
      host) - it's done to not accidentally duplicate existing IPAddress
    * then, there is check is IPAddres with new mgmt value already exist
      * if yes, there is validation if it's not assigned to any other host -
        if yes, then ValidationError is raised
      * if no, it's attached to current object and marked as management ip

    """

    def _get_management_ip(self):
        eth = (
            self.ethernet_set.select_related("ipaddress")
            .filter(ipaddress__is_management=True)
            .first()
        )
        if eth:
            return eth.ipaddress
        return None

    def _get_or_create_management_ip(self, address=None):
        ip = self._get_management_ip()

        def _create_new_ip():
            eth = self.ethernet_set.create()
            ip = IPAddress(ethernet=eth, is_management=True)
            return ip

        if not ip:
            if address:
                # check if IP is already created
                try:
                    ip = IPAddress.objects.get(address=address)
                except IPAddress.DoesNotExist:
                    ip = _create_new_ip()
                else:
                    # check if it's not assigned to any object
                    if ip.ethernet and ip.ethernet.base_object_id != self.pk:
                        raise ValidationError(
                            "IP is already assigned to {}".format(
                                ip.ethernet.base_object.last_descendant
                            )
                        )
                    # check if object has ethernet attached - if not, create new
                    # one
                    if ip.ethernet:
                        ip.ethernet.base_object = self
                        ip.ethernet.save()
                    else:
                        ip.ethernet = self.ethernet_set.create()
                    ip.is_management = True
            else:
                ip = _create_new_ip()
        return ip

    @property
    def management_ip(self):
        ip = self._get_management_ip()
        if ip:
            return ip.address
        return ""

    @management_ip.setter
    def management_ip(self, value):
        if not value:
            # this if allows to import datacenter without management ip
            del self.management_ip
            return

        current_mgmt = self.management_ip
        # if new management ip value is different than previous, remove previous
        # IP entry to not try to change it's value
        if current_mgmt and current_mgmt != value:
            del self.management_ip
        ip = self._get_or_create_management_ip(value)
        ip.address = value
        ip.save()

    @management_ip.deleter
    def management_ip(self):
        ip = self._get_management_ip()
        if ip:
            eth = ip.ethernet
            ip.delete()
            eth.delete()

    @property
    def management_hostname(self):
        ip = self._get_management_ip()
        if ip:
            return ip.hostname or ""
        return ""

    @management_hostname.setter
    def management_hostname(self, value):
        ip = self._get_or_create_management_ip()
        ip.hostname = value
        ip.save()
