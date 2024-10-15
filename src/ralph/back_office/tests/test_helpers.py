from django.test import TestCase

from ..helpers import EmailContext


class TestEmailContext(TestCase):
    def test_has_from_field(self):
        self.assertIn("from_email", EmailContext._fields)
