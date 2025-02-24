# -*- coding: utf-8 -*-
from datetime import date

from django.test import RequestFactory, TestCase
from django.urls import reverse
from djmoney.money import Money
from moneyed import PLN

from ralph.tests.mixins import ClientMixin
from ralph.tests.models import Bar, Foo


class M2MInlineTest(ClientMixin, TestCase):
    def setUp(self):
        self.foo1 = Foo.objects.create(bar="a")
        self.foo2 = Foo.objects.create(bar="b")
        self.bar1 = Bar.objects.create(
            name="Bar11", date=date(2015, 3, 1), price=Money("21.4", "PLN"), count=1
        )
        self.bar2 = Bar.objects.create(
            name="Bar22", date=date(2015, 3, 1), price=Money("21.4", "PLN"), count=1
        )
        self.foo1.bars.add(self.bar1)
        self.foo1.bars.add(self.bar2)

        self.login_as_user()
        self.factory = RequestFactory()

    def test_create_foo_with_bars(self):
        data = {
            "bar": "c",
            "_save": "Save",
            "bars-TOTAL_FORMS": 1,
            "bars-INITIAL_FORMS": 0,
            "bars-MAX_NUM_FORMS": 0,
            "bars-0-name": "Bar33",
            "bars-0-date": "2015-03-05",
            "bars-0-price_0": "10.10",
            "bars-0-price_1": "PLN",
            "bars-0-count": "10",
        }
        response = self.client.post(reverse("admin:tests_foo_add"), data)
        self.assertEqual(response.status_code, 302)
        foo = Foo.objects.get(bar="c")
        self.assertEqual(foo.bars.count(), 1)
        bar = foo.bars.all()[0]
        self.assertEqual(bar.name, "Bar33")

    def test_delete_assignment(self):
        data = {
            "bar": "a",
            "_save": "Save",
            "bars-TOTAL_FORMS": 2,
            "bars-INITIAL_FORMS": 2,
            "bars-MAX_NUM_FORMS": 0,
            "bars-0-id": self.bar1.id,
            "bars-0-name": "Bar11",
            "bars-0-date": "2015-03-01",
            "bars-0-price_0": "21.4",
            "bars-0-price_1": "PLN",
            "bars-0-count": "1",
            "bars-0-DELETE": "on",
            "bars-1-id": self.bar2.id,
            "bars-1-name": "Bar33",  # change here!
            "bars-1-date": "2016-06-06",  # change here!
            "bars-1-price_0": "11",  # change here!
            "bars-1-price_1": "PLN",  # change here!
            "bars-1-count": "11",  # change here!
        }
        response = self.client.post(
            reverse("admin:tests_foo_change", args=(self.foo1.id,)), data
        )
        self.assertEqual(response.status_code, 302)
        foo = Foo.objects.get(bar="a")
        self.assertEqual(foo.bars.count(), 1)
        bar = foo.bars.all()[0]
        self.assertEqual(bar.name, "Bar33")
        self.assertEqual(bar.date, date(2016, 6, 6))
        self.assertEqual(bar.price.amount, 11)
        self.assertEqual(bar.price.currency, PLN)
        self.assertEqual(bar.count, 11)
        # total number of Bars should not change
        self.assertEqual(Bar.objects.count(), 2)
