"""Per-rack switch configuration: the columns of the switchport grid.

``RackConfiguration`` holds the switch columns (``RackSwitchConfiguration``,
e.g. eth1/eth2/mgmt) for a rack, plus per-server exceptions
(``RackSwitchConfigurationOverride``).
"""

from django.db import models

from ralph.data_center.models import DataCenterAsset
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin


class RackConfiguration(AdminAbsoluteUrlMixin, models.Model):
    """Configuration of switches for given rack."""

    rack = models.OneToOneField(
        "data_center.Rack", on_delete=models.CASCADE, related_name="rack_configuration"
    )
    description = models.TextField(blank=True, max_length=1024)

    def __str__(self):
        return f"{self.rack} configuration"


class RackSwitchConfiguration(AdminAbsoluteUrlMixin, models.Model):
    rack_configuration = models.ForeignKey(
        RackConfiguration, on_delete=models.CASCADE, related_name="switches"
    )
    switch = models.ForeignKey(
        DataCenterAsset, on_delete=models.CASCADE, related_name="rack_switches"
    )
    label = models.CharField(
        blank=False,
        null=False,
        help_text="Switch role e.g. eth1, eth2, mgmt",
        max_length=255,
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
