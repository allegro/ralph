# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.http import QueryDict
from rest_framework.test import APIClient, APIRequestFactory

from ralph.api.filters import ExtendedFiltersBackend, LookupFilterBackend
from ralph.api.tests.api import (
    Bar,
    BarViewSet,
    Manufacturer,
    ManufacturerViewSet
)
from ralph.tests import RalphTestCase
from ralph.tests.factories import ManufacturerFactory


class TestExtendedFiltersBackend(RalphTestCase):
    def setUp(self):
        super().setUp()
        self.request_factory = APIRequestFactory()
        self.manufacture_1 = ManufacturerFactory(
            name='test', country='Poland'
        )
        self.manufacture_2 = ManufacturerFactory(
            name='test2', country='test'
        )
        get_user_model().objects.create_superuser(
            'test', 'test@test.test', 'test'
        )
        self.client = APIClient()
        self.client.login(username='test', password='test')
        self.extended_filters_backend = ExtendedFiltersBackend()

    def test_extended_filter_fields(self):
        request = self.request_factory.get('/')
        request.query_params = QueryDict(urlencode({'some_field': 'test'}))
        mvs = ManufacturerViewSet()
        mvs.request = request
        self.assertEqual(len(self.extended_filters_backend.filter_queryset(
            request, Manufacturer.objects.all(), mvs)
        ), 2)

        request.query_params = QueryDict(urlencode({'some_field': 'test2'}))
        mvs.request = request
        self.assertEqual(len(self.extended_filters_backend.filter_queryset(
            request, Manufacturer.objects.all(), mvs)
        ), 1)


class TestLookupFilterBackend(RalphTestCase):
    def setUp(self):
        super().setUp()
        self.request_factory = APIRequestFactory()
        get_user_model().objects.create_superuser(
            'test', 'test@test.test', 'test'
        )
        self.client = APIClient()
        self.client.login(username='test', password='test')

        Bar.objects.create(
            name='Bar11',
            date=date(2015, 3, 1),
            price=Decimal('21.4'),
            count=1
        )
        Bar.objects.create(
            name='Bar22',
            date=date(2014, 4, 1),
            price=Decimal('11.4'),
            count=2
        )
        Bar.objects.create(
            name='Bar33',
            date=date(2013, 5, 1),
            price=Decimal('31.4'),
            count=3
        )
        self.lookup_filter = LookupFilterBackend()

    def test_query_filters_charfield(self):
        request = self.request_factory.get('/api/bar')
        bvs = BarViewSet()
        request.query_params = QueryDict(
            urlencode({'name__icontains': 'bar1'})
        )
        bvs.request = request
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 1)

        # Failed filter
        request.query_params = QueryDict(urlencode({'name__range': 10}))
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 3)

    def test_query_filters_decimalfield(self):
        request = self.request_factory.get('/api/bar')
        bvs = BarViewSet()
        request.query_params = QueryDict(urlencode({'price__gte': 20}))
        bvs.request = request
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 2)

        # Failed filter
        request.query_params = QueryDict(urlencode({'price__istartswith': 10}))
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 3)

    def test_query_filters_integerfield(self):
        request = self.request_factory.get('/api/bar')
        bvs = BarViewSet()
        request.query_params = QueryDict(urlencode({'count__gte': 2}))
        bvs.request = request
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 2)

        # Failed filter
        request.query_params = QueryDict(urlencode({'count__istartswith': 10}))
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 3)

    def test_query_filters_datefield(self):
        request = self.request_factory.get('/api/bar')
        bvs = BarViewSet()
        request.query_params = QueryDict(urlencode({'date__year': 2015}))
        bvs.request = request
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 1)

        # Failed filter
        request.query_params = QueryDict(urlencode({'date__istartswith': 10}))
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 3)

    def test_query_filters_datetimefield(self):
        request = self.request_factory.get('/api/bar')
        bvs = BarViewSet()
        request.query_params = QueryDict(urlencode(
            {'created__year': date.today().year})
        )
        bvs.request = request
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 3)

        request.query_params = QueryDict(
            urlencode({
                'date__year': 2014,
                'created__month': date.today().month
            })
        )
        bvs.request = request
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 1)

        # Failed filter
        request.query_params = QueryDict(
            urlencode({'created__istartswith': 10})
        )
        self.assertEqual(len(self.lookup_filter.filter_queryset(
            request, Bar.objects.all(), bvs)
        ), 3)
