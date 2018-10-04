# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0006_auto_20180725_1216'),
        ('trade_marks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TradeMarksLinkedDomain',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('domain', models.ForeignKey(to='domains.Domain', related_name='trade_mark')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='trademarkslinkeddomains',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='trademarkslinkeddomains',
            name='domain',
        ),
        migrations.RemoveField(
            model_name='trademarkslinkeddomains',
            name='trade_mark',
        ),
        migrations.AlterField(
            model_name='trademark',
            name='domains',
            field=models.ManyToManyField(to='domains.Domain', related_name='_trademark_domains_+', through='trade_marks.TradeMarksLinkedDomain'),
        ),
        migrations.DeleteModel(
            name='TradeMarksLinkedDomains',
        ),
        migrations.AddField(
            model_name='trademarkslinkeddomain',
            name='trade_mark',
            field=models.ForeignKey(to='trade_marks.TradeMark'),
        ),
        migrations.AlterUniqueTogether(
            name='trademarkslinkeddomain',
            unique_together=set([('trade_mark', 'domain')]),
        ),
    ]
