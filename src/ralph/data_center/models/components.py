# -*- coding: utf-8 -*-
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.assets import Asset
from ralph.assets.models.components import Component
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin


@python_2_unicode_compatible
class DiskShare(Component):
    share_id = models.PositiveIntegerField(
        verbose_name=_("share identifier"),
        null=True,
        blank=True,
    )
    label = models.CharField(
        verbose_name=_("name"),
        max_length=255,
        blank=True,
        null=True,
        default=None,
    )
    size = models.PositiveIntegerField(
        verbose_name=_("size (MiB)"),
        null=True,
        blank=True,
    )
    snapshot_size = models.PositiveIntegerField(
        verbose_name=_("size for snapshots (MiB)"),
        null=True,
        blank=True,
    )
    wwn = NullableCharField(
        verbose_name=_("Volume serial"),
        max_length=33,
        unique=True,
    )
    full = models.BooleanField(default=True)

    def get_total_size(self):
        return (self.size or 0) + (self.snapshot_size or 0)

    class Meta:
        verbose_name = _("disk share")
        verbose_name_plural = _("disk shares")

    def __str__(self):
        return "%s (%s)" % (self.label, self.wwn)


@python_2_unicode_compatible
class DiskShareMount(AdminAbsoluteUrlMixin, models.Model):
    share = models.ForeignKey(
        DiskShare, verbose_name=_("share"), on_delete=models.CASCADE
    )
    asset = models.ForeignKey(
        Asset,
        verbose_name=_("asset"),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    volume = models.CharField(
        verbose_name=_("volume"), max_length=255, blank=True, null=True, default=None
    )
    size = models.PositiveIntegerField(
        verbose_name=_("size (MiB)"),
        null=True,
        blank=True,
    )

    def get_total_mounts(self):
        return (
            self.share.disksharemount_set.exclude(device=None)
            .filter(is_virtual=False)
            .count()
        )

    def get_size(self):
        return self.size or self.share.get_total_size()

    class Meta:
        unique_together = ("share", "asset")
        verbose_name = _("disk share mount")
        verbose_name_plural = _("disk share mounts")

    def __str__(self):
        return "%s@%r" % (self.volume, self.asset)
