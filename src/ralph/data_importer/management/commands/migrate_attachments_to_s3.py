from ralph.attachments.models import Attachment
from ralph.data_importer.management.commands._migrate_files_to_s3 import (
    MigrateFilesToS3Command,
)


class Command(MigrateFilesToS3Command):
    help = "Copy attachments from local storage to S3."
    model_fields = ((Attachment, "file"),)
