"""Netmaker validation cache and async refresh bookkeeping.

``BackendValidationResult`` caches what netmaker reports on the far side of a
switch port; ``SwitchportRefreshJob`` tracks the async rack refresh.
"""

from django.db import models

from ralph.data_center.models import DataCenterAsset
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin


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

    switch = models.ForeignKey(
        DataCenterAsset,
        on_delete=models.CASCADE,
        related_name="validation_results",
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
        unique_together = ("switch", "port_label")

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
        "RackConfiguration",
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
