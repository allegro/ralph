# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from import_export import widgets

from ralph.data_importer.models import ImportedObjects


class ImportForeignKeyMixin(object):

    """ImportForeignKeyMixin class for django import-export resources."""

    def get_or_init_instance(self, instance_loader, row):
        self.old_object_pk = row.get('id', None)
        remove_id = getattr(settings, 'REMOVE_ID_FROM_IMPORT', False)
        if remove_id:
            row['id'] = None

        return super(ImportForeignKeyMixin, self).get_or_init_instance(
            instance_loader, row
        )

    def after_save_instance(self, instance, dry_run):
        if not dry_run and self.old_object_pk:
            content_type = ContentType.objects.get_for_model(self._meta.model)
            ImportedObjects.objects.update_or_create(
                content_type=content_type,
                old_object_pk=self.old_object_pk,
                defaults={'object_pk': instance.pk}
            )

    def export_field(self, field, obj):
        """
        Override export_field.

        Each field which has widget: ForeignKeyWidget return in str format.

        Args:
            field: ImportExport field object
            obj: Django model object

        Returns:
            Value to export
        """
        if isinstance(field.widget, widgets.ForeignKeyWidget):
            try:
                return str(getattr(obj, self.get_field_name(field), ''))
            except TypeError:
                return None
        return super().export_field(field, obj)
