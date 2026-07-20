from django.db import models

from ralph.data_center.models import DataCenterAsset
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.networks.models import IPAddress


class RackConfiguration(AdminAbsoluteUrlMixin, models.Model):
    """Configuration of switches for given rack."""
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
    backend_validation = models.BooleanField(
        default=True,
        help_text=(
            "When enabled, netmaker backend validation is fetched and the "
            "netmaker column is shown for this switch in the switchport grid."
        ),
    )

    class Meta:
        unique_together = ("rack_configuration", "label")

    def __str__(self):
        return f"{self.label} -> {self.switch.hostname}"


class RackSwitchConfigurationOverride(AdminAbsoluteUrlMixin, models.Model):
    """Per-server exception to a switch column's default switch.

    A column (RackSwitchConfiguration, e.g. ``eth1``) defines the switch that
    every server in the rack connects to by default. This model is the
    exception: it lets a single ``data_center_asset`` in that rack connect its
    ``eth1`` port to a *different* switch than the column default.
    """

    rack_switch_configuration = models.ForeignKey(
        RackSwitchConfiguration,
        on_delete=models.CASCADE,
        related_name="overrides",
    )
    data_center_asset = models.ForeignKey(
        DataCenterAsset,
        on_delete=models.CASCADE,
        related_name="+",
        help_text="The server whose connection deviates from the column default.",
    )
    switch = models.ForeignKey(
        DataCenterAsset,
        on_delete=models.CASCADE,
        related_name="+",
        help_text="The alternate switch this server connects to for this column.",
    )

    class Meta:
        unique_together = ("rack_switch_configuration", "data_center_asset")

    def __str__(self):
        return (
            f"override {self.data_center_asset.hostname} "
            f"{self.rack_switch_configuration.label} -> {self.switch.hostname}"
        )


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
    oper_status = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Operational status reported by the backend (up/down/unknown)",
    )
    admin_status = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Administrative status reported by the backend (up/down/unknown)",
    )
    speed = models.IntegerField(
        null=True,
        blank=True,
        help_text="Interface speed in Mbps",
    )
    raw_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Full interface payload reported by the backend (netmaker)",
    )

    class Meta:
        unique_together = ("rack_configuration", "switch", "port_label")

    def __str__(self):
        return f"Validation {self.switch.hostname}:{self.port_label} -> {self.status}"


class RefreshJobStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    SUCCESS = "SUCCESS", "Success"
    ERROR = "ERROR", "Error"


class SwitchportRefreshJob(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    """Tracks an asynchronous netmaker refresh for a whole rack.

    A single job triggers a backend (netmaker) refresh of every switch related
    to the rack (both the column switches and the per-server override switches)
    and then pulls the fresh ports back into Ralph. Its ``status`` powers the
    in-progress / finished indicator shown in the switchport grid.
    """

    rack_configuration = models.ForeignKey(
        RackConfiguration,
        on_delete=models.CASCADE,
        related_name="refresh_jobs",
    )
    status = models.CharField(
        max_length=20,
        choices=RefreshJobStatus.choices,
        default=RefreshJobStatus.PENDING,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(
        null=True,
        blank=True,
        help_text="Per-switch counts and errors collected during the refresh.",
    )
    error = models.TextField(blank=True, default="")

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return f"Refresh {self.rack_configuration_id} [{self.status}]"

    @property
    def is_running(self) -> bool:
        return self.status in (
            RefreshJobStatus.PENDING,
            RefreshJobStatus.IN_PROGRESS,
        )
