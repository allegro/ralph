# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDecimal

from ralph.accounts.tests.factories import RegionFactory
from ralph.assets.tests.factories import (
    AssetHolderFactory,
    BackOfficeAssetModelFactory,
    BudgetInfoFactory
)
from ralph.back_office.models import (
    BackOfficeAsset,
    OfficeInfrastructure,
    Warehouse
)
from ralph.security.tests.factories import SecurityScanFactory

date_now = datetime.now().date()


class OfficeInfrastructureFactory(DjangoModelFactory):
    name = factory.Iterator(
        [
            "Office infrastructure Poland",
            "Office infrastructure Germany",
            "Office infrastructure France",
            "Office infrastructure UK",
        ]
    )

    class Meta:
        model = OfficeInfrastructure
        django_get_or_create = ["name"]


class WarehouseFactory(DjangoModelFactory):
    name = factory.Iterator(
        ["Warehouse 1", "Warehouse 2", "Warehouse 3", "Warehouse 4"]
    )

    class Meta:
        model = Warehouse
        django_get_or_create = ["name"]


class BackOfficeAssetFactory(DjangoModelFactory):
    hostname = factory.Sequence(lambda n: "c%04d" % n)
    region = factory.SubFactory(RegionFactory)
    model = factory.SubFactory(BackOfficeAssetModelFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    force_depreciation = False
    office_infrastructure = factory.SubFactory(OfficeInfrastructureFactory)
    sn = factory.Faker("ssn")
    barcode = factory.Sequence(lambda n: "bo" + str(n + 10**8))
    order_no = factory.Sequence(lambda n: "Order number " + str(n))
    budget_info = factory.SubFactory(BudgetInfoFactory)
    invoice_date = date_now - timedelta(days=15)
    invoice_no = factory.Sequence(lambda n: "Invoice number " + str(n))
    price = FuzzyDecimal(10, 300)
    securityscan = factory.RelatedFactory(SecurityScanFactory, "base_object")
    property_of = factory.SubFactory(AssetHolderFactory)

    class Meta:
        model = BackOfficeAsset
        django_get_or_create = ["sn", "barcode"]
