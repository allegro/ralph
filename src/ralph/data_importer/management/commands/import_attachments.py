# -*- coding: utf-8 -*-
import csv
import json
import logging
import os
import tempfile
import zipfile

import tablib
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from ralph.attachments.helpers import add_attachment_from_disk
from ralph.attachments.models import Attachment, AttachmentItem
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_importer.models import (
    ImportedObjectDoesNotExist,
    ImportedObjects
)
from ralph.lib.transitions.models import TransitionsHistory
from ralph.licences.models import Licence
from ralph.supports.models import Support

APP_MODELS = {model._meta.model_name: model for model in apps.get_models()}
logger = logging.getLogger(__name__)

MODELS_MAP = {
    "BackOfficeAsset": BackOfficeAsset,
    "DataCenterAsset": DataCenterAsset,
    "Support": Support,
    "Licence": Licence,
}


class Command(BaseCommand):
    help = "Imports attachments and Transition History"

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            help="zip source location",
        )
        parser.add_argument(
            "-i",
            "--import",
            choices=["attachments", "transitionshistory", "all"],
            default="all",
            dest="import",
        )

    def save_transition_history(self, directory):
        with open(os.path.join(directory, "transition_history.csv")) as f:
            reader = csv.reader(f, delimiter=",")
            csv_data = list(reader)
            headers, csv_body = csv_data[0], csv_data[1:]
            dataset = tablib.Dataset(*csv_body, headers=headers)
            for line in dataset.dict:
                model = MODELS_MAP.get(line.get("asset_type"))
                try:
                    obj = ImportedObjects.get_object_from_old_pk(
                        model, line.get("asset")
                    )
                except ImportedObjectDoesNotExist:
                    logger.warning("Missing imported object for %s", line)
                    continue

                logged_user, _ = get_user_model().objects.get_or_create(
                    username=line.get("logged_user")
                )
                new_history = False
                old_history_id = "{}|{}".format(line.get("id"), line.get("asset"))
                try:
                    history = ImportedObjects.get_object_from_old_pk(
                        TransitionsHistory, old_history_id
                    )
                except ImportedObjectDoesNotExist:
                    history = TransitionsHistory()
                    new_history = True

                history.content_type = ContentType.objects.get_for_model(model)
                history.created = line.get("created")
                history.modified = line.get("modified")
                history.logged_user = logged_user
                history.transition_name = line.get("transition")
                history.kwargs = json.loads(line.get("kwargs", {}))
                actions = [
                    i.replace("_", " ").capitalize()
                    for i in line.get("actions").split(",")
                ]
                history.actions = actions
                history.object_id = obj.pk

                if line.get("report_filename_md5"):
                    try:
                        history.attachment = Attachment.objects.get(
                            md5=line.get("report_filename_md5")
                        )
                    except Attachment.DoesNotExist:
                        try:
                            attachment = add_attachment_from_disk(
                                obj,
                                os.path.join(
                                    directory,
                                    "transition_history",
                                    "assets",
                                    line.get("report_filename"),
                                ),
                                owner=logged_user,
                            )
                            history.attachment = attachment
                        except FileNotFoundError:
                            pass

                history.save()
                # update history record using update method to skip auto_now
                # and auto_now_add fields checks
                TransitionsHistory.objects.filter(pk=history.pk).update(
                    created=line.get("created"),
                    modified=line.get("modified"),
                )
                if new_history:
                    ImportedObjects.create(history, old_history_id)

    def save_attachments(self, directory):
        with open(os.path.join(directory, "attachments.csv")) as f:
            reader = csv.reader(f, delimiter=",")
            csv_data = list(reader)
            headers, csv_body = csv_data[0], csv_data[1:]
            dataset = tablib.Dataset(*csv_body, headers=headers)
            for line in dataset.dict:
                model = MODELS_MAP.get(line.get("parent_type"), None)
                if model:
                    try:
                        obj = ImportedObjects.get_object_from_old_pk(
                            model, line.get("parents")
                        )
                    except ImportedObjectDoesNotExist:
                        logger.warning("Missing imported object for %s", line)
                        continue

                    if line.get("md5"):
                        owner, _ = get_user_model().objects.get_or_create(
                            username=line.get("uploaded_by")
                        )
                        try:
                            attachment = Attachment.objects.get(md5=line.get("md5"))
                            content_type = ContentType.objects.get_for_model(
                                obj._meta.model
                            )
                            items = attachment.items.filter(
                                object_id=obj.pk, content_type=content_type
                            )
                            if not items:
                                AttachmentItem.objects.attach(
                                    obj.pk, content_type, [attachment]
                                )
                            continue
                        except Attachment.DoesNotExist:
                            pass

                        attachment = add_attachment_from_disk(
                            obj,
                            os.path.join(directory, "attachments", line.get("file")),
                            owner=owner,
                        )
                        attachment.original_filename = line.get("original_filename")
                        attachment.save(update_fields=["original_filename"])

    def handle(self, *args, **options):
        source_file = options.get("source")
        with open(source_file, "rb") as f:
            out_path = tempfile.mkdtemp()
            z = zipfile.ZipFile(f)
            for name in z.namelist():
                z.extract(name, out_path)
            import_type = options.get("import")
            if import_type == "attachments" or import_type == "all":
                self.stdout.write("Import Attachments from: {}".format(source_file))
                self.save_attachments(out_path)
            if import_type == "transitionshistory" or import_type == "all":
                self.stdout.write(
                    "Import TransitionHistory from: {}".format(source_file)
                )
                self.save_transition_history(out_path)
