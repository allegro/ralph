# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import tempfile
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.conf import settings
from import_export import fields, resources

from ralph_assets.models_assets import Attachment, AssetType


related_name_objects = {
    'Asset': 'parents',
    'Support': 'supports',
    'Licence': 'licences',
}


def get_query_set(obj):
    """
    Returns first non-empty queryset.
    """

    qs = []
    for related in related_name_objects.values():
        qs = getattr(obj, related).all()
        if qs:
            break
    return qs


class AttachmentResource(resources.ModelResource):
    parents = fields.Field(column_name='parents')
    parent_type = fields.Field(column_name='parent_type')

    class Meta:
        fields = [
            'id',
            'original_filename',
            'uploaded_by',
            'file',
        ]
        model = Attachment

    def dehydrate_parents(self, obj):
        qs = get_query_set(obj)
        return '|'.join(map(str, qs.values_list('id', flat=True)))

    def dehydrate_parent_type(self, obj):
        qs = get_query_set(obj)
        if qs:
            cls_name = qs[0].__class__.__name__
            if cls_name == 'Asset':
                if qs[0].type == AssetType.data_center:
                    return 'DataCenterAsset'
                if qs[0].type == AssetType.back_office:
                    return 'BackOfficeAsset'
            return cls_name
        return 'None'


class Command(BaseCommand):
    help = 'Export attachments in Ralph-NG format.'

    def handle(self, *args, **options):
        model_resource = AttachmentResource()
        exclude_kwargs = {
            '{}__isnull'.format(v): True
            for v in related_name_objects.values()
        }
        lost_files = []

        with ZipFile('attachments_export.zip', 'w') as zipped:
            dirpath = tempfile.mkdtemp()
            os.chdir(dirpath)
            attachment_ids = []
            orphans = []
            for pk, f in Attachment.objects.values_list('pk', 'file').exclude(**exclude_kwargs):  # noqa
                filename = os.path.join(settings.MEDIA_ROOT, f)
                try:
                    zipped.write(filename, arcname='attachments/{}'.format(f))
                except OSError:
                    lost_files.append(f)
                else:
                    attachment_ids.append(pk)
            # add attachemnt without any connection to objects
            for pk, orphan in Attachment.objects.values_list('pk', 'file').filter(**exclude_kwargs):  # noqa
                orphans.append(orphan)
                filename = os.path.join(settings.MEDIA_ROOT, orphan)
                try:
                    zipped.write(filename, arcname='orphans/{}'.format(orphan))
                except OSError:
                    lost_files.append(orphan)
            dataset = model_resource.export(Attachment.objects.filter(pk__in=attachment_ids).exclude(file=''))  # noqa
            with open('attachments.csv', 'wb') as output_file:
                output_file.write(dataset.csv)
            with open('lost_files.txt', 'w') as output_file:
                output_file.write('\n'.join(lost_files))
            with open('orphans.txt', 'w') as output_file:
                output_file.write('\n'.join(orphans))
            zipped.write('attachments.csv')
            zipped.write('lost_files.txt')
            zipped.write('orphans.txt')
