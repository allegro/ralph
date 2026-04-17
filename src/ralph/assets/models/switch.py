from django.db import models

from django.utils.translation import gettext_lazy as _

from ralph.assets.models import AssetModel, BaseObject, Ethernet
from ralph.assets.models.choices import EthernetSpeed
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, NamedMixin


class SwitchTemplate(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    switch_model = models.ForeignKey(
        AssetModel, on_delete=models.CASCADE, related_name="switch_templates"
    )
    port_count = models.PositiveIntegerField()
    prefix = models.CharField(help_text="e.g. et-0/0/", max_length=64)
    speed = models.CharField(choices=EthernetSpeed(), max_length=32)


class SwitchPort(AdminAbsoluteUrlMixin, models.Model):
    base_object = models.ForeignKey(
        BaseObject, related_name="switchports_set", on_delete=models.CASCADE
    )
    name = models.CharField(_("name"), max_length=255)
    speed = models.CharField(choices=EthernetSpeed(), max_length=32)
    remote_port = models.ForeignKey(
        Ethernet, on_delete=models.SET_NULL, null=True, blank=True, default=None
    )

    class Meta:
        unique_together = ("base_object", "name")
