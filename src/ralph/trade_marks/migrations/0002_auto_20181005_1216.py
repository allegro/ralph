# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade_marks', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel('TradeMarksLinkedDomains','TradeMarksLinkedDomain')
    ]
