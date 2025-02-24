# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('title', models.CharField(max_length=100)),
                ('content', models.CharField(max_length=1000)),
                ('custom_field_1', models.CharField(max_length=100, blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Foo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('bar', models.CharField(max_length=50, verbose_name='bar')),
            ],
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
            ],
        ),
        migrations.CreateModel(
            name='LongArticle',
            fields=[
                ('article_ptr', models.OneToOneField(serialize=False, primary_key=True, to='permissions_tests.Article', parent_link=True, auto_created=True, on_delete=django.db.models.deletion.CASCADE)),
                ('remarks', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('permissions_tests.article',),
        ),
        migrations.AddField(
            model_name='library',
            name='articles',
            field=models.ManyToManyField(to='permissions_tests.Article', related_name='library_articles'),
        ),
        migrations.AddField(
            model_name='library',
            name='lead_article',
            field=models.ForeignKey(to='permissions_tests.Article', related_name='library_lead', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='article',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='articles_author', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='article',
            name='collaborators',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='articles_collaborator'),
        ),
        migrations.AddField(
            model_name='longarticle',
            name='custom_field_2',
            field=models.ForeignKey(related_name='long_article', null=True, to='permissions_tests.Article', blank=True, on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
