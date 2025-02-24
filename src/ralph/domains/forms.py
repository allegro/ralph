from django.forms import CheckboxSelectMultiple
from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphAdminForm
from ralph.domains.models import Domain
from ralph.lib.mixins.forms import PriceFormMixin


class DomainForm(RalphAdminForm):
    class Meta:
        model = Domain
        exclude = []
        widgets = {
            "additional_services": CheckboxSelectMultiple,
        }


class DomainContractForm(PriceFormMixin, RalphAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].help_text = _("Price for domain renewal for given period")
