# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ralph.accounts.tests.factories import RegionFactory
from ralph.assets.tests.factories import AssetHolderFactory, BudgetInfoFactory
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.supports.models import (
    BaseObjectsSupport,
    Support,
    SupportStatus,
    SupportType
)

date_now = datetime.now().date()


class SupportTypeFactory(DjangoModelFactory):
    name = factory.Iterator(["warranty", "additional"])

    class Meta:
        model = SupportType
        django_get_or_create = ["name"]


class SupportFactory(DjangoModelFactory):
    region = factory.SubFactory(RegionFactory)
    support_type = factory.SubFactory(SupportTypeFactory)
    status = SupportStatus.new
    contract_id = factory.Sequence(lambda n: "c{}".format(n))
    date_to = date(2020, 12, 31)
    name = factory.Iterator(
        [
            "cisco",
            "hp",
            "ibm",
            "intel",
            "dell",
            "sun",
            "google",
            "juniper",
            "2hp",
            "ironport",
            "microsoft",
            "oracle",
            "3par",
            "tk",
        ]
    )
    date_from = date_now - timedelta(days=15)
    date_to = date_now + timedelta(days=365)
    producer = factory.Iterator(
        [
            "cisco",
            "hp",
            "ibm",
            "intel",
            "dell",
            "sun",
            "google",
            "juniper",
            "2hp",
            "ironport",
            "microsoft",
            "oracle",
            "3par",
            "tk",
        ]
    )
    serial_no = FuzzyText()
    invoice_no = factory.Sequence(lambda n: "Invoice number " + str(n))
    invoice_date = date_now - timedelta(days=15)
    budget_info = factory.SubFactory(BudgetInfoFactory)
    property_of = factory.SubFactory(AssetHolderFactory)

    class Meta:
        model = Support


class BaseObjectsSupportFactory(DjangoModelFactory):
    baseobject = factory.SubFactory(BackOfficeAssetFactory)
    support = factory.SubFactory(SupportFactory)

    class Meta:
        model = BaseObjectsSupport


class BackOfficeAssetSupportFactory(BaseObjectsSupportFactory):
    pass


class DataCenterAssetSupportFactory(BaseObjectsSupportFactory):
    baseobject = factory.SubFactory(DataCenterAssetFactory)
