"""Physical connection graph: ports, connections and their members.

A ``Connection`` groups two (or more) ``Port`` objects via ``ConnectionMember``.
These models know nothing about racks or netmaker validation.
"""

from django.db import models

from ralph.data_center.models import DataCenterAsset
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.networks.models import IPAddress


class AddressReservation(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    local_address = models.OneToOneField(
        IPAddress, on_delete=models.CASCADE, related_name="local_address_reservation"
    )
    remote_address = models.OneToOneField(
        IPAddress, on_delete=models.CASCADE, related_name="remote_address_reservation"
    )


class Port(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    label = models.CharField(blank=False, null=False, max_length=255, db_index=True)
    data_center_asset = models.ForeignKey(
        DataCenterAsset,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="ports",
    )
    address_reservation = models.OneToOneField(
        AddressReservation, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"Port (id={self.pk}, label={self.label}, of={self.data_center_asset.hostname})"

    class Meta:
        unique_together = ("label", "data_center_asset")


class Connection(models.Model):
    def __str__(self):
        ports = self.members.select_related("port").all()
        names = " <-> ".join(str(m.port) for m in ports)
        return names or f"Connection #{self.pk}"


class ConnectionMember(models.Model):
    connection = models.ForeignKey(
        Connection,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="members",
    )
    port = models.OneToOneField(
        Port,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="connectionmember",
    )

    def __str__(self):
        return str(self.port)
