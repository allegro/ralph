# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

from ralph.domains.models.domains import WebsiteType
from ralph.domains.publishers import _publish_domain_data
from ralph.domains.tests.factories import DomainFactory


class TestDomainValidation(TestCase):
    def test_pass_when_type_redirect_and_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.redirect.id,
            website_url="www.allegro.pl",
        )
        domain.clean()

    def test_raise_error_when_type_redirect_and_no_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.redirect.id,
            website_url="",
        )
        with self.assertRaises(ValidationError):
            domain.clean()

    def test_pass_when_type_none_and_no_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.none.id,
            website_url="",
        )
        domain.clean()

    def test_raise_error_when_type_none_and_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.none.id,
            website_url="www.allegro.pl",
        )
        with self.assertRaises(ValidationError):
            domain.clean()

    def test_pass_when_type_direct_and_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.direct.id,
            website_url="www.allegro.pl",
        )
        domain.clean()

    def test_pass_when_type_direct_and_no_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.direct.id,
            website_url="",
        )
        domain.clean()


class TestDomainUpdateSignal(TestCase):
    def test_domain_update_returns_domain_name(self):
        domain = DomainFactory()

        result = _publish_domain_data(domain)

        self.assertEqual(domain.name, result["domain_name"])

    def test_domain_update_returns_business_owners(self):
        domain = DomainFactory(technical_owner=None)

        result = _publish_domain_data(domain)

        self.assertEqual(
            [
                {
                    "username": domain.business_owner.username,
                    "ownership_type": settings.DOMAIN_OWNER_TYPE["BO"],
                }
            ],
            result["owners"],
        )

    def test_domain_update_returns_technical_owners(self):
        domain = DomainFactory(business_owner=None)

        result = _publish_domain_data(domain)

        self.assertEqual(
            [
                {
                    "username": domain.technical_owner.username,
                    "ownership_type": settings.DOMAIN_OWNER_TYPE["TO"],
                }
            ],
            result["owners"],
        )

    def test_domain_update_returns_empty_owners_when_no_owners(self):
        domain = DomainFactory(business_owner=None, technical_owner=None)

        result = _publish_domain_data(domain)

        self.assertEqual(result["owners"], [])

    def test_domain_update_returns_service_uid(self):
        domain = DomainFactory()

        result = _publish_domain_data(domain)

        self.assertEqual(domain.service.uid, result["service_uid"])

    def test_domain_update_returns_empty_when_no_service(self):
        domain = DomainFactory()
        domain.service_env = None
        domain.save()

        result = _publish_domain_data(domain)

        self.assertEqual(result["service_uid"], "")
