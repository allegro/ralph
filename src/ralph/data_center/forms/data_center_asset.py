from ralph.admin.mixins import RalphAdminForm
from ralph.data_center.models.physical import DataCenterAsset


class DataCenterAssetForm(RalphAdminForm):
    def clean_hostname(self):
        # TODO: NullableCharField instead of normal CharField in model
        hostname = self.cleaned_data['hostname']
        if hostname and not len(hostname.strip()):
            hostname = None
        return hostname

    class Meta:
        model = DataCenterAsset
        exclude = ()
