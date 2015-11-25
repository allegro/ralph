# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import ralph.attachments.helpers


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('md5', models.CharField(unique=True, max_length=32)),
                ('original_filename', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to=ralph.attachments.helpers.get_file_path, max_length=255)),
                ('mime_type', models.CharField(default='application/octet-stream', max_length=100)),
                ('description', models.TextField(blank=True)),
                ('uploaded_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'ordering': ('-modified', '-created'),
            },
        ),
        migrations.CreateModel(
            name='AttachmentItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('attachment', models.ForeignKey(to='attachments.Attachment', related_name='items')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
    ]
