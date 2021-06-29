from django.forms import CheckboxSelectMultiple
from django.utils.translation import ugettext_lazy as _

from ralph.admin.mixins import RalphAdminForm
from ralph.trade_marks.models import Design, Patent, TradeMark


class IntellectualPropertyForm(RalphAdminForm):
    class Meta:
        fields = ['additional_markings']
        widgets = {
            'additional_markings': CheckboxSelectMultiple,
        }


class TradeMarkForm(IntellectualPropertyForm):
    class Meta(IntellectualPropertyForm.Meta):
        model = TradeMark
        labels = {
            'name': _('Trade Mark Name'),
        }


class DesignForm(IntellectualPropertyForm):
    class Meta(IntellectualPropertyForm.Meta):
        model = Design
        labels = {
            'name': _('Design Name'),
        }


class PatentForm(IntellectualPropertyForm):
    class Meta(IntellectualPropertyForm.Meta):
        model = Patent
        labels = {
            'name': _('Patent Name'),
        }
