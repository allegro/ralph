# -*- coding: utf-8 -*-
from collections import OrderedDict

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from import_export import fields, widgets

from ralph.data_importer.models import ImportedObjects
from ralph.data_importer.widgets import (
    ExportForeignKeyStrWidget,
    ExportManyToManyStrTroughWidget,
    ExportManyToManyStrWidget,
    ManyToManyThroughWidget
)


class ImportForeignKeyMeta(type):
    def __new__(cls, name, bases, attrs):
        """
        Add additional fields to the export_class.fields with *_str
        for display ForeignKey fields.
        """
        # https://bugs.python.org/issue29270
        attrs.pop("__classcell__", None)
        new_class = super().__new__(cls, name, bases, attrs)
        # Generate second class only for export which has added
        # additional *_str fields
        export_class = super().__new__(cls, "{}Exporter".format(name), bases, attrs)
        update_fields = []
        for name, field in new_class.fields.items():
            update_fields.append((name, field))
            field_name = "{}_str".format(name)
            field_params = dict(
                column_name="{}_str".format(field.column_name),
                attribute=field.attribute,
                readonly=True,
            )
            # skip str field if pointer implicitly
            if getattr(field, "_skip_str_field", False):
                continue
            elif isinstance(field.widget, widgets.ForeignKeyWidget):
                field_params["widget"] = ExportForeignKeyStrWidget()
            elif isinstance(field.widget, ManyToManyThroughWidget):
                field_params["widget"] = ExportManyToManyStrTroughWidget(
                    model=field.widget.model,
                    related_model=field.widget.related_model,
                    through_field=field.widget.through_field,
                )
            elif isinstance(field.widget, widgets.ManyToManyWidget):
                field_params["widget"] = ExportManyToManyStrWidget(
                    model=field.widget.model
                )
            else:
                continue
            new_field = fields.Field(**field_params)
            # rewrite field extra attributes
            for extra_param_name in [
                # if set to True, foreign key will not be added automatically
                # to `select_related` - usefull when it's need to be fetched
                # using `prefetch_related` (ex. for `parent` field with more
                # logic in fetching it)
                "_exclude_in_select_related"
            ]:
                if hasattr(field, extra_param_name):
                    setattr(
                        new_field, extra_param_name, getattr(field, extra_param_name)
                    )
            update_fields.append((field_name, new_field))
        export_class.fields = OrderedDict(update_fields)
        new_class.export_class = export_class
        return new_class


class ImportForeignKeyMixin(object):
    """ImportForeignKeyMixin class for django import-export resources."""

    def get_or_init_instance(self, instance_loader, row):
        self.old_object_pk = row.get("id", None)
        remove_id = getattr(settings, "REMOVE_ID_FROM_IMPORT", False)
        if remove_id:
            row["id"] = None

        return super(ImportForeignKeyMixin, self).get_or_init_instance(
            instance_loader, row
        )

    def after_save_instance(
        self, instance, using_transactions: bool, dry_run: bool, *args, **kwargs
    ):
        if not dry_run and self.old_object_pk:
            content_type = ContentType.objects.get_for_model(self._meta.model)
            ImportedObjects.objects.update_or_create(
                content_type=content_type,
                old_object_pk=self.old_object_pk,
                defaults={"object_pk": instance.pk},
            )

    def import_field(self, field, obj, data, is_m2m=False):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        if field.column_name == "management_ip":
            field.save(obj, data, is_m2m=False)
        elif field.attribute and field.column_name in data:
            field.save(obj, data, is_m2m)
