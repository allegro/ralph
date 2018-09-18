from django.forms import CheckboxSelectMultiple

from ralph.admin.mixins import RalphAdminForm
from ralph.trade_marks.models import TradeMark


class IntellectualPropertyForm(RalphAdminForm):
    class Meta:
        model = TradeMark
        exclude = []
        widgets = {
            'additional_markings': CheckboxSelectMultiple,
        }
