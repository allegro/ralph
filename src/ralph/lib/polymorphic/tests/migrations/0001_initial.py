# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PolymorphicModelBaseTest',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SomethingRelated',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PolymorphicModelTest',
            fields=[
                ('polymorphicmodelbasetest_ptr', models.OneToOneField(auto_created=True, to='polymorphic_tests.PolymorphicModelBaseTest', serialize=False, parent_link=True, primary_key=True, on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('polymorphic_tests.polymorphicmodelbasetest', models.Model),
        ),
        migrations.CreateModel(
            name='PolymorphicModelTest2',
            fields=[
                ('polymorphicmodelbasetest_ptr', models.OneToOneField(auto_created=True, to='polymorphic_tests.PolymorphicModelBaseTest', serialize=False, parent_link=True, primary_key=True, on_delete=django.db.models.deletion.CASCADE)),
                ('another_related', models.ForeignKey(to='polymorphic_tests.SomethingRelated', null=True, blank=True, related_name='+', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=('polymorphic_tests.polymorphicmodelbasetest', models.Model),
        ),
        migrations.AddField(
            model_name='polymorphicmodelbasetest',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, blank=True, on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='polymorphicmodelbasetest',
            name='sth_related',
            field=models.ForeignKey(to='polymorphic_tests.SomethingRelated', null=True, blank=True, on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
