from django.forms import CheckboxSelectMultiple

from ralph.admin.mixins import RalphAdminForm
from ralph.trade_marks.models import TradeMarks


class IntellectualPropertyForm(RalphAdminForm):
    class Meta:
        model = TradeMarks
        exclude = []
        widgets = {
            'additional_markings': CheckboxSelectMultiple,
        }
