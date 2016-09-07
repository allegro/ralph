# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.test import TestCase

from ralph.domains.models.domains import WebsiteType
from ralph.domains.tests.factories import DomainFactory


class TestDomainValidation(TestCase):
    def test_pass_when_type_redirect_and_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.redirect.id, website_url='www.allegro.pl',
        )
        domain.clean()

    def test_raise_error_when_type_redirect_and_no_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.redirect.id, website_url='',
        )
        with self.assertRaises(ValidationError):
            domain.clean()

    def test_pass_when_type_none_and_no_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.none.id, website_url='',
        )
        domain.clean()

    def test_raise_error_when_type_none_and_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.none.id, website_url='www.allegro.pl',
        )
        with self.assertRaises(ValidationError):
            domain.clean()

    def test_pass_when_type_direct_and_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.direct.id, website_url='www.allegro.pl',
        )
        domain.clean()

    def test_pass_when_type_direct_and_no_value(self):
        domain = DomainFactory(
            website_type=WebsiteType.direct.id, website_url='',
        )
        domain.clean()
