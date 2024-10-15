from django.forms import CheckboxSelectMultiple

from ralph.admin.mixins import RalphAdminForm
from ralph.sim_cards.models import SIMCard


class SIMCardForm(RalphAdminForm):
    class Meta:
        model = SIMCard
        exclude = []
        widgets = {
            "features": CheckboxSelectMultiple,
        }
