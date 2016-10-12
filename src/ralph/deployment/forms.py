from unittest.mock import MagicMock

from django import forms
from django.template import TemplateSyntaxError

from ralph.admin.mixins import RalphAdminFormMixin
from ralph.deployment.models import PrebootConfiguration, PrebootItemType
from ralph.deployment.utils import _render_configuration


class PrebootConfigurationForm(RalphAdminFormMixin, forms.ModelForm):
    class Meta:
        model = PrebootConfiguration
        fields = ('name', 'type', 'configuration')

    def is_valid(self):
        is_valid = super().is_valid()
        try:
            _render_configuration(
                self.cleaned_data.get('configuration', ''), MagicMock(),
                disable_reverse=True
            )
        except TemplateSyntaxError as error:
            self.add_error('configuration', error)
            is_valid = False
        return is_valid

    def clean_configuration(self):
        configuration_type = self.cleaned_data.get('type')
        configuration = self.cleaned_data.get('configuration')
        if configuration_type == PrebootItemType.kickstart.id:
            if 'done_url' not in configuration:
                raise forms.ValidationError(
                    'Please specify {{ done_url }} (e.g. curl {{ done_url }})'
                )
        return configuration
