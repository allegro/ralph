from ralph.data_importer.management.commands._migrate_files_to_s3 import (
    MigrateFilesToS3Command,
)
from ralph.reports.models import ReportTemplate


class Command(MigrateFilesToS3Command):
    help = "Copy report templates from local storage to S3."
    model_fields = ((ReportTemplate, "template"),)
