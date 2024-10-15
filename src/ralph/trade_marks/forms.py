from django.forms import CheckboxSelectMultiple

from ralph.admin.mixins import RalphAdminForm
from ralph.trade_marks.models import Design, Patent, TradeMark, UtilityModel


class IntellectualPropertyForm(RalphAdminForm):
    class Meta:
        fields = ["additional_markings"]
        widgets = {
            "additional_markings": CheckboxSelectMultiple,
        }


class TradeMarkForm(IntellectualPropertyForm):
    class Meta(IntellectualPropertyForm.Meta):
        model = TradeMark


class DesignForm(IntellectualPropertyForm):
    class Meta(IntellectualPropertyForm.Meta):
        model = Design


class PatentForm(IntellectualPropertyForm):
    class Meta(IntellectualPropertyForm.Meta):
        model = Patent


class UtilityModelForm(IntellectualPropertyForm):
    class Meta(IntellectualPropertyForm.Meta):
        model = UtilityModel
