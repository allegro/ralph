from unittest.mock import MagicMock

import yaml
from django import forms
from django.template import TemplateSyntaxError

from ralph.admin.mixins import RalphAdminFormMixin
from ralph.deployment.models import PrebootConfiguration, PrebootItemType
from ralph.deployment.utils import _render_configuration


class PrebootConfigurationForm(RalphAdminFormMixin, forms.ModelForm):
    class Meta:
        model = PrebootConfiguration
        fields = ("name", "type", "configuration")

    def is_valid(self):
        is_valid = super().is_valid()
        try:
            configuration = _render_configuration(
                self.cleaned_data.get("configuration", ""),
                MagicMock(),
                disable_reverse=True,
            )
        except TemplateSyntaxError as error:
            self.add_error("configuration", error)
            return False
        configuration_type = self.cleaned_data.get("type")
        if configuration_type in (PrebootItemType.meta_data, PrebootItemType.user_data):
            try:
                yaml.load(configuration, Loader=yaml.FullLoader)
            except yaml.YAMLError as error:
                self.add_error("configuration", error)
                return False
        return is_valid

    def clean_configuration(self):
        configuration_type = self.cleaned_data.get("type")
        configuration = self.cleaned_data.get("configuration")
        if configuration_type in (
            PrebootItemType.kickstart.id,
            PrebootItemType.preseed.id,
            PrebootItemType.user_data.id,
        ):
            if "done_url" not in configuration:
                raise forms.ValidationError(
                    "Please specify {{ done_url }} (e.g. curl {{ done_url }})"
                )
        return configuration
