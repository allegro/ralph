from django import forms

from ralph.admin.mixins import RalphAdminFormMixin
from ralph.deployment.models import PrebootItemType


class PrebootConfigurationForm(RalphAdminFormMixin, forms.ModelForm):
    def clean_configuration(self):
        configuration_type = self.cleaned_data['type']
        configuration = self.cleaned_data['configuration']
        if configuration_type == PrebootItemType.kickstart.id:
            if 'done_url' not in configuration:
                raise forms.ValidationError(
                    'Please specify {{ done_url }} (e.g. curl {{ done_url }})'
                )
        return configuration
