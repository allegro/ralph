from django.test import TestCase

from ralph.deployment.forms import PrebootConfigurationForm


class TestForm(TestCase):
    def test_invalid_configuration(self):
        form_data = {
            "configuration": "{% foo bar %} wrong template tag",
            "type": 1,
            "name": "test",
        }
        form = PrebootConfigurationForm(data=form_data)
        self.assertFalse(form.is_valid())
