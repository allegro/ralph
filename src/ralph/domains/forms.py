from django.forms import CheckboxSelectMultiple

from ralph.admin.mixins import RalphAdminForm
from ralph.domains.models import Domain


class DomainForm(RalphAdminForm):
    class Meta:
        model = Domain
        exclude = []
        widgets = {
            'additional_services': CheckboxSelectMultiple,
        }
