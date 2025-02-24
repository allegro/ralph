# -*- coding: utf-8 -*-
from collections import OrderedDict

from dj.choices import Choices
from rest_framework.exceptions import ValidationError

from ralph.api.fields import ReversedChoiceField, StrField
from ralph.tests import RalphTestCase
from ralph.tests.models import Foo


class TestChoices(Choices):
    _ = Choices.Choice

    foo = _("foo11")
    bar = _("bar22")


class TestStrField(RalphTestCase):
    def setUp(self):
        self.foo = Foo(bar="abc")
        self.str_field = StrField()
        self.str_field_with_type = StrField(show_type=True)

    def test_str_field_representation(self):
        self.assertEqual(self.str_field.to_representation(self.foo), str(self.foo))

    def test_str_field_with_type(self):
        self.assertEqual(
            self.str_field_with_type.to_representation(self.foo),
            "{}: {}".format(Foo._meta.verbose_name, str(self.foo)),
        )


class TestReversedChoiceField(RalphTestCase):
    def setUp(self):
        self.reversed_choice_field = ReversedChoiceField(TestChoices())

    def test_reversed_choices(self):
        self.assertEqual(
            self.reversed_choice_field.reversed_choices,
            OrderedDict([("foo11", TestChoices.foo.id), ("bar22", TestChoices.bar.id)]),
        )

    def test_to_representation_should_return_choice_text(self):
        self.assertEqual(
            self.reversed_choice_field.to_representation(TestChoices.foo.id), "foo11"
        )

    def test_to_internal_value_should_map_choice_text_to_id(self):
        self.assertEqual(
            self.reversed_choice_field.to_internal_value("foo11"),
            TestChoices.foo.id,
        )

    def test_to_internal_value_with_choice_not_found_should_raise_validation_error(
        self,
    ):  # noqa
        with self.assertRaises(ValidationError):
            self.reversed_choice_field.to_internal_value("foo33")
