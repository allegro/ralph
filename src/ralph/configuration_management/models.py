from dj.choices import Choices
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import BaseObject
from ralph.lib.mixins.models import TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin


class SCMScanStatus(Choices):
    _ = Choices.Choice

    ok = _("ok")
    fail = _("fail")
    error = _("error")


class SCMScan(
    PermByFieldMixin,
    TimeStampMixin,
    models.Model
):
    """Represents software configuration management scan."""

    base_object = models.OneToOneField(BaseObject, on_delete=models.CASCADE)
    last_scan_date = models.DateTimeField(
        blank=False, null=False,
        verbose_name=_("Last SCM scan date")
    )
    scan_status = models.PositiveIntegerField(
        choices=SCMScanStatus(),
        blank=False,
        null=False,
        verbose_name=_("SCM scan status")
    )
