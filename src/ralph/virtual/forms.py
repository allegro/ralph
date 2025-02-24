import json

from django import forms
from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphAdminFormMixin
from ralph.virtual.models import CloudProvider


class CloudProviderForm(RalphAdminFormMixin, forms.ModelForm):
    class Meta:
        model = CloudProvider
        fields = ("name", "cloud_sync_enabled", "cloud_sync_driver", "client_config")

    def clean_client_config(self):
        try:
            client_config = self.cleaned_data.get("client_config")

            if client_config:
                json.loads(client_config)

            return client_config
        except json.JSONDecodeError as error:
            self.add_error("client_config", error)
            raise forms.ValidationError(
                _("Client configuration must be a valid JSON text.")
            )
