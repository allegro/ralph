from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _

from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, NamedMixin


class ServiceBasedVisibilityScope(AdminAbsoluteUrlMixin, NamedMixin):
    services = models.ManyToManyField(
        "assets.Service", related_name="visibility_scopes", blank=True
    )
    group = models.ForeignKey(
        Group,
        related_name="visibility_scopes",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("Service-based Visibility Scope")
