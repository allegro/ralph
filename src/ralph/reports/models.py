from django.db import models

from ralph.attachments.helpers import get_file_path
from ralph.lib.mixins.models import NamedMixin, TimeStampMixin


def get_report_file_path(instance, filename):
    return get_file_path(
        instance, filename, default_dir='report_templates'
    )


class Report(NamedMixin, TimeStampMixin, models.Model):
    pass


class ReportLanguage(NamedMixin, TimeStampMixin, models.Model):
    pass


class ReportTemplate(TimeStampMixin, models.Model):
    template = models.FileField(
        upload_to=get_report_file_path,
        blank=False,
    )
    language = models.ForeignKey(ReportLanguage)
    default = models.BooleanField()
    report = models.ForeignKey(
        Report,
        related_name='templates',
    )

    class Meta:
        unique_together = ('language', 'report')

    def __str__(self):
        return '{} ({})'.format(self.template, self.language)

    @property
    def name(self):
        return self.report.name
