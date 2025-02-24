# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf import settings
from django.db import migrations, models

import ralph.lib.mixins.models
import ralph.trade_marks.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("domains", "0007_auto_20200909_1012"),
        ("assets", "0032_auto_20200909_1012"),
        ("trade_marks", "0007_auto_20190813_0914"),
    ]

    operations = [
        migrations.CreateModel(
            name="Design",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                        parent_link=True,
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "registrant_number",
                    models.CharField(verbose_name="Registrant number", max_length=255),
                ),
                (
                    "type",
                    models.PositiveIntegerField(
                        verbose_name="Trade Mark type",
                        default=2,
                        choices=[
                            (1, "Word"),
                            (2, "Figurative"),
                            (3, "Word - Figurative"),
                        ],
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=ralph.trade_marks.models.upload_dir,
                    ),
                ),
                (
                    "registrant_class",
                    models.CharField(verbose_name="Registrant class", max_length=255),
                ),
                ("valid_from", models.DateField(blank=True, null=True)),
                ("valid_to", models.DateField(blank=True, null=True)),
                (
                    "order_number_url",
                    models.URLField(max_length=255, blank=True, null=True),
                ),
                (
                    "status",
                    models.PositiveIntegerField(
                        verbose_name="Trade Mark status",
                        default=5,
                        choices=[
                            (1, "Application filed"),
                            (2, "Application refused"),
                            (3, "Application withdrawn"),
                            (4, "Application opposed"),
                            (5, "Registered"),
                            (6, "Registration invalidated"),
                            (7, "Registration expired"),
                        ],
                    ),
                ),
                (
                    "additional_markings",
                    models.ManyToManyField(
                        blank=True, to="trade_marks.ProviderAdditionalMarking"
                    ),
                ),
                (
                    "business_owner",
                    models.ForeignKey(
                        related_name="design_business_owner",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, "assets.baseobject"),
        ),
        migrations.CreateModel(
            name="DesignAdditionalCountry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "country",
                    models.ForeignKey(
                        to="trade_marks.TradeMarkCountry",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "design",
                    models.ForeignKey(
                        to="trade_marks.Design",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Design Additional Country",
                "verbose_name_plural": "Design Additional Countries",
            },
        ),
        migrations.CreateModel(
            name="DesignsLinkedDomains",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "design",
                    models.ForeignKey(
                        to="trade_marks.Design",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "domain",
                    models.ForeignKey(
                        related_name="design",
                        to="domains.Domain",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Design Linked Domain",
                "verbose_name_plural": "Design Linked Domains",
            },
        ),
        migrations.CreateModel(
            name="Patent",
            fields=[
                (
                    "baseobject_ptr",
                    models.OneToOneField(
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                        parent_link=True,
                        to="assets.BaseObject",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "registrant_number",
                    models.CharField(verbose_name="Registrant number", max_length=255),
                ),
                (
                    "type",
                    models.PositiveIntegerField(
                        verbose_name="Trade Mark type",
                        default=2,
                        choices=[
                            (1, "Word"),
                            (2, "Figurative"),
                            (3, "Word - Figurative"),
                        ],
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=ralph.trade_marks.models.upload_dir,
                    ),
                ),
                (
                    "registrant_class",
                    models.CharField(verbose_name="Registrant class", max_length=255),
                ),
                ("valid_from", models.DateField(blank=True, null=True)),
                ("valid_to", models.DateField(blank=True, null=True)),
                (
                    "order_number_url",
                    models.URLField(max_length=255, blank=True, null=True),
                ),
                (
                    "status",
                    models.PositiveIntegerField(
                        verbose_name="Trade Mark status",
                        default=5,
                        choices=[
                            (1, "Application filed"),
                            (2, "Application refused"),
                            (3, "Application withdrawn"),
                            (4, "Application opposed"),
                            (5, "Registered"),
                            (6, "Registration invalidated"),
                            (7, "Registration expired"),
                        ],
                    ),
                ),
                (
                    "additional_markings",
                    models.ManyToManyField(
                        blank=True, to="trade_marks.ProviderAdditionalMarking"
                    ),
                ),
                (
                    "business_owner",
                    models.ForeignKey(
                        related_name="patent_business_owner",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, "assets.baseobject"),
        ),
        migrations.CreateModel(
            name="PatentAdditionalCountry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "country",
                    models.ForeignKey(
                        to="trade_marks.TradeMarkCountry",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "patent",
                    models.ForeignKey(
                        to="trade_marks.Patent",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Patent Additional Country",
                "verbose_name_plural": "Patent Additional Countries",
            },
        ),
        migrations.CreateModel(
            name="PatentsLinkedDomains",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "domain",
                    models.ForeignKey(
                        related_name="patent",
                        to="domains.Domain",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "patent",
                    models.ForeignKey(
                        to="trade_marks.Patent",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Patent Linked Domain",
                "verbose_name_plural": "Patent Linked Domains",
            },
        ),
        migrations.AlterField(
            model_name="trademark",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.AddField(
            model_name="patent",
            name="domains",
            field=models.ManyToManyField(
                related_name="_patent_domains_+",
                to="domains.Domain",
                through="trade_marks.PatentsLinkedDomains",
            ),
        ),
        migrations.AddField(
            model_name="patent",
            name="holder",
            field=models.ForeignKey(
                verbose_name="Trade Mark holder",
                blank=True,
                null=True,
                to="assets.AssetHolder",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="patent",
            name="registrar_institution",
            field=models.ForeignKey(
                null=True,
                to="trade_marks.TradeMarkRegistrarInstitution",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="patent",
            name="technical_owner",
            field=models.ForeignKey(
                related_name="patent_technical_owner",
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="design",
            name="domains",
            field=models.ManyToManyField(
                related_name="_design_domains_+",
                to="domains.Domain",
                through="trade_marks.DesignsLinkedDomains",
            ),
        ),
        migrations.AddField(
            model_name="design",
            name="holder",
            field=models.ForeignKey(
                verbose_name="Trade Mark holder",
                blank=True,
                null=True,
                to="assets.AssetHolder",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="design",
            name="registrar_institution",
            field=models.ForeignKey(
                null=True,
                to="trade_marks.TradeMarkRegistrarInstitution",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="design",
            name="technical_owner",
            field=models.ForeignKey(
                related_name="design_technical_owner",
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="patentslinkeddomains",
            unique_together=set([("patent", "domain")]),
        ),
        migrations.AlterUniqueTogether(
            name="patentadditionalcountry",
            unique_together=set([("country", "patent")]),
        ),
        migrations.AlterUniqueTogether(
            name="designslinkeddomains",
            unique_together=set([("design", "domain")]),
        ),
        migrations.AlterUniqueTogether(
            name="designadditionalcountry",
            unique_together=set([("country", "design")]),
        ),
    ]
