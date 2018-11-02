from django.forms import CheckboxSelectMultiple

from ralph.admin.mixins import RalphAdminForm
from ralph.trade_marks.models import TradeMark


class IntellectualPropertyForm(RalphAdminForm):
    class Meta:
        model = TradeMark
        fields = ['additional_markings']
        widgets = {
            'additional_markings': CheckboxSelectMultiple,
        }
