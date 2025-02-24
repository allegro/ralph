# -*- coding: utf-8 -*-
import datetime

from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from ralph.accounts.tests.factories import UserFactory
from ralph.admin.filters import (
    BooleanListFilter,
    ChoicesListFilter,
    date_format_to_human,
    DateListFilter,
    IPFilter,
    LiquidatedStatusFilter,
    NumberListFilter,
    RelatedAutocompleteFieldListFilter,
    RelatedFieldListFilter,
    TagsListFilter,
    TextListFilter,
    TreeRelatedAutocompleteFilterWithDescendants
)
from ralph.admin.sites import ralph_site
from ralph.assets.tests.factories import (
    ConfigurationClassFactory,
    ConfigurationModuleFactory
)
from ralph.data_center.admin import DataCenterAssetAdmin
from ralph.data_center.models.physical import (
    DataCenterAsset,
    DataCenterAssetStatus
)
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory
)
from ralph.supports.admin import SupportAdmin
from ralph.supports.models import Support
from ralph.supports.tests.factories import SupportFactory
from ralph.tests.admin import Car2Admin, CarAdmin
from ralph.tests.models import Car, Car2


class AdminFiltersTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.conf_module1 = ConfigurationModuleFactory(name="abc")
        cls.conf_module2 = ConfigurationModuleFactory(parent=cls.conf_module1)
        cls.conf_class = ConfigurationClassFactory(module=cls.conf_module2)
        cls.dca_1 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 1, 1),
            barcode="barcode_one",
            status=DataCenterAssetStatus.new,
        )
        cls.dca_1.tags.add("tag_1")
        cls.dca_2 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 2, 1),
            barcode="barcode_two",
            status=DataCenterAssetStatus.liquidated,
        )
        cls.dca_2.management_ip = "10.20.30.40"
        cls.dca_2.tags.add("tag_1")
        cls.dca_3 = DataCenterAssetFactory(
            invoice_date=datetime.date(2015, 3, 1),
            force_depreciation=True,
            status=DataCenterAssetStatus.used,
        )
        cls.dca_3.tags.add("tag1")
        cls.dca_3.tags.add("tag2")
        cls.dca_4 = DataCenterAssetFactory(
            invoice_date=datetime.date(2014, 3, 1),
            rack=RackFactory(),
            configuration_path=cls.conf_class,
        )
        cls.dca_4.tags.add("tag1")
        cls.support_1 = SupportFactory(price=10)
        cls.support_2 = SupportFactory(price=100)

    def add_session_to_request(self, request):
        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

    def test_date_format_to_human(self):
        self.assertEqual("YYYY-MM-DD", date_format_to_human("%Y-%m-%d"))
        self.assertEqual("YY-DD-MM", date_format_to_human("%y-%d-%m"))

    def test_boolean_filter(self):
        boolean_filter = BooleanListFilter(
            field=DataCenterAsset._meta.get_field("force_depreciation"),
            request=None,
            params={"force_depreciation": True},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="force_depreciation",
        )
        queryset = boolean_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_3.pk, queryset.first().pk)

    def test_choices_filter(self):
        choices_filter = ChoicesListFilter(
            field=DataCenterAsset._meta.get_field("status"),
            request=None,
            params={"status": DataCenterAssetStatus.new},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="status",
        )
        queryset = choices_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

        choices_filter = ChoicesListFilter(
            field=DataCenterAsset._meta.get_field("status"),
            request=None,
            params={"status": DataCenterAssetStatus.used},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="status",
        )
        queryset = choices_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(1, queryset.count())

    def test_text_filter(self):
        text_filter = TextListFilter(
            field=DataCenterAsset._meta.get_field("barcode"),
            request=None,
            params={"barcode": "barcode_one"},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="barcode",
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_1.pk, queryset.first().pk)

    def test_text_filter_with_separator(self):
        text_filter = TextListFilter(
            field=DataCenterAsset._meta.get_field("barcode"),
            request=None,
            params={"barcode": "barcode_one|barcode_two"},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="barcode",
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_text_filter_with_separator_and_whitespace(self):
        text_filter = TextListFilter(
            field=DataCenterAsset._meta.get_field("barcode"),
            request=None,
            params={"barcode": " barcode_one | barcode_two"},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="barcode",
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_text_filter_contains(self):
        text_filter = TextListFilter(
            field=DataCenterAsset._meta.get_field("barcode"),
            request=None,
            params={"barcode": "one"},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="barcode",
        )
        queryset = text_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(self.dca_1.pk, queryset.first().pk)

    def test_tags_filter(self):
        tags_filter = TagsListFilter(
            request=None,
            params={"tags": "tag1 & tag2"},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = tags_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(len(queryset), 1)

        tags_filter = TagsListFilter(
            request=None,
            params={"tags": "tag1"},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = tags_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(len(queryset), 2)

    def test_date_filter(self):
        datet_filter = DateListFilter(
            field=DataCenterAsset._meta.get_field("invoice_date"),
            request=None,
            params={
                "invoice_date__start": "2015-01-20",
                "invoice_date__end": "2015-04-01",
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="invoice_date",
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_date_filter_start(self):
        datet_filter = DateListFilter(
            field=DataCenterAsset._meta.get_field("invoice_date"),
            request=None,
            params={
                "invoice_date__start": "2015-02-1",
                "invoice_date__end": "",
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="invoice_date",
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(2, queryset.count())

    def test_date_filter_end(self):
        datet_filter = DateListFilter(
            field=DataCenterAsset._meta.get_field("invoice_date"),
            request=None,
            params={
                "invoice_date__start": "",
                "invoice_date__end": "2015-02-20",
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="invoice_date",
        )
        queryset = datet_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(3, queryset.count())

    def test_related_field(self):
        related_filter = RelatedFieldListFilter(
            field=DataCenterAsset._meta.get_field("rack"),
            request=None,
            params={
                "rack": self.dca_4.rack.id,
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="rack",
        )
        queryset = related_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(1, queryset.count())

    def test_tree_related_field_with_descendants(self):
        related_filter = TreeRelatedAutocompleteFilterWithDescendants(
            field=(
                DataCenterAsset._meta.get_field(
                    "configuration_path"
                ).remote_field.model._meta.get_field("module")
            ),
            request=None,
            params={
                "configuration_path__module": str(self.conf_module1.id),
            },
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
            field_path="configuration_path__module",
        )
        queryset = related_filter.queryset(None, DataCenterAsset.objects.all())

        self.assertEqual(1, queryset.count())

    def test_decimal_filter(self):
        datet_filter = NumberListFilter(
            field=Support._meta.get_field("price"),
            request=None,
            params={
                "price__start": 0,
                "price__end": 200,
            },
            model=Support,
            model_admin=SupportAdmin,
            field_path="price",
        )
        queryset = datet_filter.queryset(None, Support.objects.all())

        self.assertEqual(2, queryset.count())

    def test_decimal_filter_start(self):
        datet_filter = NumberListFilter(
            field=Support._meta.get_field("price"),
            request=None,
            params={
                "price__start": 50,
                "price__end": "",
            },
            model=Support,
            model_admin=SupportAdmin,
            field_path="price",
        )
        queryset = datet_filter.queryset(None, Support.objects.all())

        self.assertEqual(1, queryset.count())

    def test_decimal_filter_end(self):
        datet_filter = NumberListFilter(
            field=Support._meta.get_field("price"),
            request=None,
            params={
                "price__start": "",
                "price__end": 50,
            },
            model=Support,
            model_admin=SupportAdmin,
            field_path="price",
        )
        queryset = datet_filter.queryset(None, Support.objects.all())

        self.assertEqual(1, queryset.count())

    def test_liquidated_status_filter(self):
        liquidated_filter = LiquidatedStatusFilter(
            request=None,
            params={"liquidated": "1"},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = liquidated_filter.queryset(None, DataCenterAsset.objects.all())
        self.assertEqual(4, queryset.count())

        liquidated_filter = LiquidatedStatusFilter(
            request=None,
            params={"liquidated": None},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = liquidated_filter.queryset(None, DataCenterAsset.objects.all())
        self.assertEqual(3, queryset.count())

    def test_filter_title(self):
        related_filter = RelatedFieldListFilter(
            field=Car._meta.get_field("manufacturer"),
            request=None,
            params={
                "manufacturer": 1,
            },
            model=Car,
            model_admin=CarAdmin,
            field_path="manufacturer",
        )
        self.assertEqual("test", related_filter.title)

    def test_is_not_autocomplete(self):
        list_filter = CarAdmin.list_filter
        CarAdmin.list_filter = ["manufacturer"]
        request = RequestFactory().get("/")
        request.user = UserFactory(is_superuser=True, is_staff=True)
        self.add_session_to_request(request)
        car_admin = CarAdmin(Car, ralph_site)
        change_list = car_admin.changelist_view(request)
        filters = change_list.context_data["cl"].get_filters(request)

        self.assertTrue(isinstance(filters[0][0], RelatedFieldListFilter))
        CarAdmin.list_filter = list_filter

    def test_is_autocomplete(self):
        request = RequestFactory().get("/")
        request.user = UserFactory(is_superuser=True, is_staff=True)
        self.add_session_to_request(request)
        car_admin = Car2Admin(Car2, ralph_site)
        change_list = car_admin.changelist_view(request)
        filters = change_list.context_data["cl"].get_filters(request)

        self.assertTrue(isinstance(filters[0][0], RelatedAutocompleteFieldListFilter))

    def test_incorrect_value_related(self):
        request = RequestFactory().get("/")
        # ugly hack from https://code.djangoproject.com/ticket/17971
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        related_filter = RelatedAutocompleteFieldListFilter(
            field=Car._meta.get_field("manufacturer"),
            request=request,
            params={
                "manufacturer": "string",
            },
            model=Car,
            model_admin=CarAdmin,
            field_path="manufacturer",
        )
        with self.assertRaises(IncorrectLookupParameters):
            related_filter.queryset(request, Car.objects.all())

    def test_ip_address_filter(self):
        ipaddress_filter = IPFilter(
            request=None,
            params={"ip": "10.20.30.40"},
            model=DataCenterAsset,
            model_admin=DataCenterAssetAdmin,
        )
        queryset = ipaddress_filter.queryset(None, DataCenterAsset.objects.all())
        self.assertEqual(1, queryset.count())
