from django.core.checks import Error
from django.test import TestCase

from ralph.lib.transitions.checks import check_transition_templates
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.tests.models import Order


class TestChecks(TransitionTestCase):
    def test_empty(self):
        errors = check_transition_templates(None)
        expected_errors = []
        self.assertEqual(expected_errors, errors)

    def test_transition_templates_should_be_a_list_or_tuple(self):
        errors = check_transition_templates('template')
        expected_errors = [
            Error(
                'TRANSITION_TEMPLATES must be a list or a tuple',
                id='transitions.E001'
            )
        ]
        self.assertEqual(expected_errors, errors)

    def test_transition_templates_should_exist(self):
        errors = check_transition_templates((
            ('transitions/run_transition.html', 'Standard template'),
        ))
        expected_errors = []
        self.assertEqual(expected_errors, errors)

    def test_transition_templates_item_should_be_two_elements_tuple(self):
        errors = check_transition_templates((
            ('broken',),
            1234,
            'foo-bar.html'
        ))
        expected_errors = [
            Error(
                'Element #0 must be a two elements tuple',
                id='transitions.E003'
            ),
            Error(
                'Element #1 must be a two elements tuple',
                id='transitions.E003'
            ),
            Error(
                'Element #2 must be a two elements tuple',
                id='transitions.E003'
            ),
        ]
        self.assertEqual(expected_errors, errors)

    def test_transition_templates_without_settings(self):
        _, transition, _ = self._create_transition(Order, 'test')
        transition.template_name = 'foo/bar.html'
        transition.save()
        errors = check_transition_templates(None)
        expected_errors = [
            Error(
                'Template foo/bar.html for test transition is defined only'
                ' in transition',
                hint='Change your TRANSITION_TEMPLATES settings by adding '
                '(foo/bar.html, "Your template name") and '
                'then edit test transition',
                id='transitions.E004'
            ),
        ]
        self.assertEqual(expected_errors, errors)
