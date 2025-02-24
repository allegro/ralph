from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.attachments.helpers import get_file_path
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)


def get_report_file_path(instance, filename):
    return get_file_path(instance, filename, default_dir="report_templates")


class Report(AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model):
    pass


class ReportLanguage(AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model):
    default = models.BooleanField()

    def clean(self):
        default_qs = self.__class__.objects.filter(default=True)
        if self.pk:
            default_qs = default_qs.exclude(pk=self.pk)
        if self.default and default_qs.count() > 0:
            raise ValidationError(_("Only one language can be default."))


class ReportTemplate(TimeStampMixin, models.Model):
    template = models.FileField(
        upload_to=get_report_file_path,
        blank=False,
    )
    language = models.ForeignKey(ReportLanguage, on_delete=models.CASCADE)
    default = models.BooleanField()
    report = models.ForeignKey(
        Report, related_name="templates", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("language", "report")

    def __str__(self):
        return "{} ({})".format(self.template, self.language)

    @property
    def name(self):
        return self.report.name
