# -*- coding: utf-8 -*-
import csv
import glob
import logging
import os
import tempfile
import zipfile

import reversion
import tablib
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from import_export import resources

from ralph.data_importer import resources as ralph_resources
from ralph.data_importer.models import ImportedObjects
from ralph.data_importer.resources import RalphModelResource

APP_MODELS = {model._meta.model_name: model for model in apps.get_models()}
logger = logging.getLogger(__name__)


def get_resource(model_name):
    """Return resource for import model."""
    resource_name = model_name + "Resource"
    resource = getattr(ralph_resources, resource_name, None)
    if not resource:
        model_class = APP_MODELS[model_name.lower()]
        resource = resources.modelresource_factory(
            model=model_class, resource_class=RalphModelResource
        )
    return resource()


class Command(BaseCommand):
    help = "Imports data for specified model from specified file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model_name",
            help="The model name to which the import data",
        )
        parser.add_argument(
            "source",
            help="file, zip or dir source location",
        )
        parser.add_argument(
            "--skipid",
            action="store_true",
            default=False,
            help="Remove ID value from rows",
        )
        parser.add_argument(
            "-t", "--type", choices=["file", "dir", "zip"], default="file", dest="type"
        )
        parser.add_argument(
            "-d",
            "--delimiter",
            dest="delimiter",
            default=",",
            help="Delimiter for csv file",
        )
        parser.add_argument(
            "-e",
            "--encoding",
            dest="encoding",
            default="utf-8",
            help="Output encoding",
        )
        parser.add_argument(
            "--map-imported-id-to-new-id",
            dest="map_imported_id_to_new_id",
            default=False,
            action="store_true",
            help="Use it when importing data from Ralph 2.",
        )

    def from_zip(self, options):
        with open(options.get("source"), "rb") as f:
            out_path = tempfile.mkdtemp()
            z = zipfile.ZipFile(f)
            for name in z.namelist():
                z.extract(name, out_path)
            options["source"] = out_path
            self.from_dir(options)

    def from_dir(self, options):
        file_list = []
        for path in glob.glob(os.path.join(options.get("source"), "*.csv")):
            base_name = os.path.basename(path)
            file_name = os.path.splitext(base_name)[0].split("_")
            file_list.append(
                {"model": file_name[1], "path": path, "sort": int(file_name[0])}
            )
        file_list = sorted(file_list, key=lambda x: x["sort"])
        for item in file_list:
            logger.info("Import to model: {}".format(item["model"]))
            options["model_name"] = item["model"]
            options["source"] = item["path"]
            self.from_file(options)

    def delete_objs(self, data, model):
        counter = 0
        for old_id in data:
            revision_manager = reversion.default_revision_manager
            if not old_id:
                continue
            obj = ImportedObjects.get_object_from_old_pk(model, int(old_id))
            revision_manager.save_revision((obj,), comment="Imported from old Ralph")
            with reversion.create_revision():
                obj.delete()
            counter += 1
        return counter

    def from_file(self, options):
        if not options.get("model_name"):
            raise CommandError("You must select a model")
        csv.register_dialect("RalphImporter", delimiter=str(options["delimiter"]))
        settings.REMOVE_ID_FROM_IMPORT = options.get("skipid")
        self.stdout.write(
            "Import {} resource from {}".format(
                options.get("model_name"), options.get("source")
            )
        )
        with open(options.get("source")) as csv_file:
            reader_kwargs = {}
            reader = csv.reader(csv_file, dialect="RalphImporter", **reader_kwargs)
            csv_data = list(reader)
            headers, csv_body = csv_data[0], csv_data[1:]
            model_resource = get_resource(options.get("model_name"))
            before_import = model_resource._meta.model.objects.count()
            dataset = tablib.Dataset(*csv_body, headers=headers)
            objs_delete = [
                obj.get("id", None)
                for obj in dataset.dict
                if int(obj.get("deleted", 0)) == 1
            ]
            result = model_resource.import_data(dataset, dry_run=False)
            if result.has_errors():
                for idx, row in enumerate(result.rows):
                    for error in row.errors:
                        error_msg = "\n".join(
                            [
                                "line_number: {}".format(idx + 1),
                                "error message: {}".format(error.error),
                                "row data: {}".format(list(zip(headers, dataset[idx]))),
                                "",
                            ]
                        )
                        self.stderr.write(error_msg)
                    if row.errors:
                        break
            after_import_count = model_resource._meta.model.objects.count()

            self.stderr.write(
                "Imported records: {}".format(after_import_count - before_import)
            )
            if len(csv_body) - after_import_count - before_import >= 0:
                self.stderr.write(
                    "Skipped records: {}".format(
                        len(csv_body) - after_import_count - before_import
                    )
                )

            deleted = self.delete_objs(objs_delete, model_resource._meta.model)
            self.stdout.write("{} deleted\n".format(deleted))
            self.stdout.write("Done\n")

    def handle(self, *args, **options):
        if options.get("map_imported_id_to_new_id"):
            settings.MAP_IMPORTED_ID_TO_NEW_ID = True
        settings.CHECK_IP_HOSTNAME_ON_SAVE = False
        if options.get("type") == "dir":
            self.from_dir(options)
        elif options.get("type") == "zip":
            self.from_zip(options)
        else:
            self.from_file(options)
