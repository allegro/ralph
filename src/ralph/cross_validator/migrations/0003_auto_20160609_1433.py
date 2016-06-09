# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields.json
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('cross_validator', '0002_auto_20160609_1409'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ignored',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('object_pk', models.IntegerField(db_index=True)),
                ('field', models.CharField(db_index=True, max_length=50)),
                ('old', ralph.lib.mixins.fields.NullableCharField(null=True, db_index=True, max_length=255)),
                ('new', ralph.lib.mixins.fields.NullableCharField(null=True, db_index=True, max_length=255)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='result',
            name='ignored',
            field=django_extensions.db.fields.json.JSONField(),
        ),
    ]
