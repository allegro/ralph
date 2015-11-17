# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import os
import tempfile
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.conf import settings
from import_export import fields, resources
from ralph_assets.models_transition import TransitionsHistory
from ralph_assets.models_assets import Attachment, AssetType


related_name_objects = {
    'Asset': ['parents', 'parents'],
    'Support': ['support', 'support_set'],
    'Licence': ['licence', 'licence_set'],
}


def get_query_set(obj):
    """
    Returns first non-empty queryset.
    """
    qs = []
    for related in related_name_objects.values():
        qs = getattr(obj, related[1]).all()
        if qs:
            break
    return qs


class TransitionsHistoryResource(resources.ModelResource):

    id = fields.Field('id', column_name='id')
    asset = fields.Field('asset', column_name='asset')
    asset_type = fields.Field('asset_type', column_name='asset_type')
    actions = fields.Field('actions', column_name='actions')
    logged_user = fields.Field('logged_user', column_name='logged_user')
    transition = fields.Field('transition', column_name='transition')
    report_filename = fields.Field(
        'report_filename', column_name='report_filename'
    )
    report_filename_md5 = fields.Field(
        'report_filename_md5', column_name='report_filename_md5'
    )
    created = fields.Field('created', column_name='created')
    modified = fields.Field('modified', column_name='modified')

    def dehydrate_id(self, history):
        return history.transitionshistory.pk

    def dehydrate_created(self, history):
        return history.transitionshistory.created

    def dehydrate_modified(self, history):
        return history.transitionshistory.modified

    def dehydrate_report_filename(self, history):
        return history.transitionshistory.report_filename

    def dehydrate_report_filename_md5(self, history):
        md5 = ''
        try:
            md5 = hashlib.md5(
                history.transitionshistory.report_file.read()
            ).hexdigest() if history.transitionshistory.report_file else ''
        except IOError:
            pass
        return md5

    def dehydrate_transition(self, history):
        return history.transitionshistory.transition.slug

    def dehydrate_logged_user(self, history):
        return history.transitionshistory.logged_user.username \
            if history.transitionshistory.logged_user_id else ''

    def dehydrate_asset_type(self, history):
        if history.asset.asset_type == AssetType.data_center:
            return 'DataCenterAsset'
        else:
            return 'BackOfficeAsset'

    def dehydrate_asset(self, history):
        return history.asset_id

    def dehydrate_actions(self, history):
        return ",".join(history.transitionshistory.transition.actions_names)

    def get_queryset(self):
        qs = TransitionsHistory.assets.through.objects.all()
        qs = qs.select_related(
            'transitionshistory', 'asset', 'transitionshistory__logged_user'
        ).prefetch_related('transitionshistory__transition__actions')
        return qs


class AttachmentResource(resources.ModelResource):
    parents = fields.Field(column_name='parents')
    parent_type = fields.Field(column_name='parent_type')
    md5 = fields.Field(column_name='md5')

    class Meta:
        fields = [
            'id',
            'original_filename',
            'uploaded_by',
            'file',
        ]
        model = Attachment

    def dehydrate_md5(self, obj):
        return hashlib.md5(obj.file.read()).hexdigest() if obj.file else ''

    def dehydrate_parents(self, obj):
        qs = get_query_set(obj)
        return '|'.join(map(str, qs.values_list('id', flat=True)))

    def dehydrate_uploaded_by(self, obj):
        return obj.uploaded_by.username if obj.uploaded_by_id else ''

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
            '{}__isnull'.format(v[0]): True
            for v in related_name_objects.values()
        }
        lost_files = []
        transition_lost_files = []

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

            history = TransitionsHistory.objects.all().values_list(
                'pk', 'report_file'
            ).filter(report_file__isnull=False)
            for pk, report_file in history:
                filename = os.path.join(settings.MEDIA_ROOT, report_file)
                if report_file:
                    try:
                        zipped.write(
                            filename,
                            arcname='transition_history/{}'.format(report_file)
                        )
                    except OSError:
                        transition_lost_files.append(report_file)

            dataset = model_resource.export(Attachment.objects.filter(pk__in=attachment_ids).exclude(file=''))  # noqa
            with open('attachments.csv', 'wb') as output_file:
                output_file.write(dataset.csv)
            with open('lost_files.txt', 'w') as output_file:
                output_file.write('\n'.join(lost_files))
            with open('orphans.txt', 'w') as output_file:
                output_file.write('\n'.join(orphans))

            transition_resource = TransitionsHistoryResource()
            with open('transition_history.csv', 'wb') as output_file:
                output_file.write(transition_resource.export().csv)

            with open('lost_transition_history.txt', 'w') as output_file:
                output_file.write('\n'.join(transition_lost_files))

            zipped.write('attachments.csv')
            zipped.write('transition_history.csv')
            zipped.write('lost_transition_history.txt')
            zipped.write('lost_files.txt')
            zipped.write('orphans.txt')
