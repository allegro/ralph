from django.db import models

from ralph.data_center.models import DataCenterAsset
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.networks.models import IPAddress


class RackConfiguration(AdminAbsoluteUrlMixin, models.Model):
    rack = models.OneToOneField(
        "data_center.Rack", on_delete=models.CASCADE, related_name="rack_configuration"
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.rack} configuration"


class RackSwitchConfiguration(AdminAbsoluteUrlMixin, models.Model):
    rack_configuration = models.ForeignKey(
        RackConfiguration, on_delete=models.CASCADE, related_name="switches"
    )
    switch = models.ForeignKey(
        DataCenterAsset, on_delete=models.CASCADE, related_name="rack_switches"
    )
    label = models.TextField(
        blank=False,
        null=False,
        help_text="Switch role e.g. eth1, eth2, mgmt",
        db_index=True,
    )

    class Meta:
        unique_together = ("rack_configuration", "label")


class AddressReservation(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    local_address = models.OneToOneField(
        IPAddress, on_delete=models.CASCADE, related_name="local_address_reservation"
    )
    remote_address = models.OneToOneField(
        IPAddress, on_delete=models.CASCADE, related_name="remote_address_reservation"
    )


class Port(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    label = models.CharField(max_length=255)
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


class ValidationStatus(models.TextChoices):
    SWITCH_NOT_FOUND = "SWITCH_NOT_FOUND", "Switch not found in backend"
    PORT_NOT_FOUND = "PORT_NOT_FOUND", "Port not found on switch"
    ASSET_FOUND = "ASSET_FOUND", "Asset found on port"
    ASSET_CONFLICT = "ASSET_CONFLICT", "Conflicting assets reported by backend"


class BackendValidationResult(TimeStampMixin, models.Model):
    """Cache of netmaker backend validation for a specific switch port.

    Stores what the backend (netmaker) reports is connected on the other side
    of a given switch port.
    """

    rack_configuration = models.ForeignKey(
        RackConfiguration,
        on_delete=models.CASCADE,
        related_name="validation_results",
    )
    switch = models.ForeignKey(
        DataCenterAsset,
        on_delete=models.CASCADE,
        related_name="+",
    )
    port_label = models.CharField(
        max_length=255,
        help_text="Switch port label, e.g. 0/0/20",
    )
    status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
    )
    remote_asset = models.ForeignKey(
        DataCenterAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="The asset found on the other side of this port (if resolved)",
    )
    remote_hostname = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Raw hostname reported by LLDP (even if not matched to a Ralph asset)",
    )

    class Meta:
        unique_together = ("rack_configuration", "switch", "port_label")

    def __str__(self):
        return f"Validation {self.switch.hostname}:{self.port_label} -> {self.status}"
