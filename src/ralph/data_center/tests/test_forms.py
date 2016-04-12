# -*- coding: utf-8 -*-
from django.forms import ValidationError

from ralph.networks.forms import validate_is_management
from ralph.tests import RalphTestCase


class EmptyForm:
    cleaned_data = None


class NetworkLineFormsetTest(RalphTestCase):

    def test_validate_one_management(self):
        form_1 = EmptyForm()
        form_1.cleaned_data = {
            'DELETE': False,
            'is_management': True,
        }
        form_2 = EmptyForm()
        form_2.cleaned_data = {
            'DELETE': False,
            'is_management': True,
        }
        with self.assertRaisesRegex(
            ValidationError,
            (
                'Only one managment IP address can be assigned '
                'to this asset'
            )
        ):
            validate_is_management([form_1, form_2])
