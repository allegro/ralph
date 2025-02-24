# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.reports.models import Report, ReportLanguage, ReportTemplate


class ReportFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "Report {}".format(n))

    class Meta:
        model = Report


class ReportLanguageFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "Report-lang {}".format(n))
    default = False

    class Meta:
        model = ReportLanguage


class ReportTemplateFactory(DjangoModelFactory):
    template = factory.django.FileField(filename="the_file.dat")
    language = factory.SubFactory(ReportLanguageFactory)
    default = False
    report = factory.SubFactory(ReportFactory)

    class Meta:
        model = ReportTemplate
