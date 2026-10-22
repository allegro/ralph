from ralph.data_importer.management.commands._migrate_files_to_s3 import (
    MigrateFilesToS3Command,
)
from ralph.trade_marks.models import Design, Patent, TradeMark, UtilityModel


class Command(MigrateFilesToS3Command):
    help = "Copy trade mark, patent, design and utility model images to S3."
    model_fields = (
        (TradeMark, "image"),
        (Patent, "image"),
        (Design, "image"),
        (UtilityModel, "image"),
    )
