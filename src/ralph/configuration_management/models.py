from dj.choices import Choices
from dj.choices.fields import ChoiceField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import BaseObject
from ralph.lib.mixins.models import TimeStampMixin
from ralph.lib.permissions.models import PermByFieldMixin


class SCMCheckResult(Choices):
    _ = Choices.Choice

    scm_ok = _("OK").extra(alert="success", icon_class="fa-check-circle")
    check_failed = _("Check failed").extra(
        alert="warning", icon_class="fa-question-circle"
    )
    scm_error = _("Error").extra(alert="alert", icon_class="fa-exclamation-triangle")


class SCMStatusCheck(PermByFieldMixin, TimeStampMixin, models.Model):
    """Represents software configuration management scan."""

    base_object = models.OneToOneField(BaseObject, on_delete=models.CASCADE)
    last_checked = models.DateTimeField(
        blank=False, null=False, verbose_name=_("Last SCM check")
    )
    check_result = ChoiceField(
        choices=SCMCheckResult,
        blank=False,
        null=False,
        verbose_name=_("SCM check result"),
    )
    ok = models.BooleanField(default=False, editable=False)

    def save(self, *args, **kwargs):
        self.ok = self.check_result == SCMCheckResult.scm_ok.id
        super().save(*args, **kwargs)
