from django import forms

from ralph.admin.mixins import RalphAdminForm
from ralph.data_center.models.physical import DataCenterAsset


class DataCenterAssetForm(RalphAdminForm):
    management_ip = forms.IPAddressField(required=False)
    management_hostname = forms.CharField(required=False)

    ip_fields = ['management_ip', 'management_hostname']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.ip_fields:
            self.fields[field].initial = getattr(self.instance, field)

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        obj.management_ip = self.cleaned_data['management_ip']
        obj.management_hostname = self.cleaned_data['management_hostname']
        return obj

    class Meta:
        model = DataCenterAsset
        exclude = ()
