from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError


class MigrateFilesToS3Command(BaseCommand):
    """Shared implementation for the per-model media backfill commands."""

    model_fields = ()

    def handle(self, *args, **options):
        copied = 0
        already_present = 0
        missing = []

        for model, field_name in self.model_fields:
            storage = model._meta.get_field(field_name).storage
            if not hasattr(storage, "copy_local_to_s3"):
                raise CommandError("The default file storage does not support S3 migration.")
            if not storage.s3_enabled:
                raise CommandError(
                    "S3 storage is not enabled. Configure AWS_STORAGE_BUCKET_NAME "
                    "and S3_STORAGE_ENABLED before running this command."
                )

            self.stdout.write("Copying {}.{} files...".format(model.__name__, field_name))
            queryset = model._default_manager.all().only("pk", field_name)
            for obj in queryset.iterator():
                file_field = getattr(obj, field_name)
                if not file_field:
                    continue
                try:
                    was_copied = storage.copy_local_to_s3(file_field.name)
                except FileNotFoundError:
                    missing.append(file_field.name)
                    self.stderr.write(
                        "Local media file is missing: {} ({} pk={})".format(
                            file_field.name, model.__name__, obj.pk
                        )
                    )
                    continue
                except ImproperlyConfigured as error:
                    raise CommandError(str(error)) from error

                if was_copied:
                    copied += 1
                else:
                    already_present += 1

        summary = "S3 migration complete: {} copied, {} already present, {} missing.".format(
            copied, already_present, len(missing)
        )
        if missing:
            raise CommandError(
                "{} Restore or clean up the missing files and rerun the command.".format(summary)
            )
        self.stdout.write(self.style.SUCCESS(summary))
