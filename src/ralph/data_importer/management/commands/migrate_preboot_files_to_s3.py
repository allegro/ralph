from ralph.data_importer.management.commands._migrate_files_to_s3 import (
    MigrateFilesToS3Command,
)
from ralph.deployment.models import PrebootFile


class Command(MigrateFilesToS3Command):
    help = "Copy preboot files from local storage to S3."
    model_fields = ((PrebootFile, "file"),)
