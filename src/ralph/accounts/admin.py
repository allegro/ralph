# -*- coding: utf-8 -*-
from string import Formatter
from urllib.parse import quote_plus, urlencode

from django.conf import settings
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from reversion import revisions as reversion

from ralph.accounts.models import RalphUser, Region, Team
from ralph.admin.decorators import register
from ralph.admin.helpers import getattr_dunder
from ralph.admin.mixins import RalphAdmin, RalphAdminFormMixin
from ralph.admin.views.extra import RalphDetailView
from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus
from ralph.lib.table.table import Table
from ralph.lib.transitions.models import TransitionsHistory
from ralph.licences.models import Licence
from ralph.sim_cards.models import SIMCard

# use string for whole app (app_label) or tuple (app_label, model_name) to
# exclude particular model
PERMISSIONS_EXCLUDE = [
    "admin",
    "attachment",
    "authtoken",
    "contenttypes",
    "data_importer",
    "reversion",
    "sessions",
    "sitetree",
    "taggit",
    ("assets", "assetlasthostname"),
    ("transitions", "action"),
    ("transitions", "transitionshistory"),
    ("transitions", "transitionmodel"),
]


def quotation_to_inches(text):
    """Replace quotation by unicode inches sign."""
    return text.replace('"', "\u2033")


class EditPermissionsFormMixin(object):
    def _simplify_permissions(self, queryset):
        """
        Exclude some permissions from widget.

        Permissions to exclude are defined in PERMISSIONS_EXCLUDE.
        """
        queryset = queryset.exclude(
            content_type__app_label__in=[
                ct for ct in PERMISSIONS_EXCLUDE if not isinstance(ct, (tuple, list))
            ]
        )
        for value in PERMISSIONS_EXCLUDE:
            if isinstance(value, (tuple, list)):
                app_label, model_name = value
                queryset = queryset.exclude(
                    content_type__app_label=app_label, content_type__model=model_name
                )
        queryset = queryset.select_related("content_type").order_by(
            "content_type__model"
        )
        return queryset


class RalphUserChangeForm(
    EditPermissionsFormMixin, RalphAdminFormMixin, UserAdmin.form
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields.get("user_permissions", None)
        if field:
            self._simplify_permissions(field.queryset)

    def clean_password(self):
        """
        Override django.contrib.auth.forms.UserChangeForm.

        We're not showing password field so we need to skip this method
        to prevent KeyError.
        """
        pass


class AssetList(Table):
    def buyout_date(self, item):
        if item.status in [
            BackOfficeAssetStatus.in_use_team.id,
            BackOfficeAssetStatus.in_use_test.id,
        ]:
            return ""
        if item.model.category.show_buyout_date:
            return item.buyout_date
        return "&mdash;"

    buyout_date.title = _("Buyout date")

    def user_licence(self, item):
        licences = item.licences.select_related("licence")
        if licences:
            result = [
                '<a href="{}">{}</a><br />'.format(
                    reverse(
                        "admin:licences_licence_change", args=(licence.licence.pk,)
                    ),
                    licence.licence,
                )
                for licence in licences
            ]
            return ["".join(result)]
        else:
            return []

    def buyout_ticket(self, item):
        if not item.model.category.show_buyout_date:
            return ""
        if item.status is not BackOfficeAssetStatus.used.id:
            return ""
        else:
            get_params = {
                "inventory_number": item.barcode,
                "serial_number": item.sn,
                "model": quotation_to_inches(str(item.model)),
                "comment": item.buyout_date,
            }
            url = "?".join([settings.MY_EQUIPMENT_BUYOUT_URL, urlencode(get_params)])
            url_title = "Report buyout"
            return self.create_report_link(url, url_title, item)

    buyout_ticket.title = "buyout_ticket"

    def report_failure(self, item):
        url = settings.MY_EQUIPMENT_REPORT_FAILURE_URL
        url_title = "Report failure"
        return self.create_report_link(url, url_title, item)

    report_failure.title = ""

    def create_report_link(self, url, url_title, item):
        item_dict = model_to_dict(item)
        if url:
            placeholders = [k[1] for k in Formatter().parse(url) if k[1] is not None]
            item_dict.update({k: getattr_dunder(item, k) for k in placeholders})
            if self.request and "username" not in item_dict:
                item_dict["username"] = self.request.user.username

            def escape_param(p):
                """
                Escape URL param and replace quotation by unicode inches sign
                """
                return quote_plus(quotation_to_inches(str(p)))

            return '<a href="{}" target="_blank">{}</a><br />'.format(
                url.format(**{k: escape_param(v) for (k, v) in item_dict.items()}),
                _(url_title),
            )
        return ""

    def confirm_ownership(self, item):
        has_inv_tag = any(
            [n.startswith(settings.INVENTORY_TAG) for n in item.tags.names()]
        )
        if not (item.warehouse.stocktaking_enabled or item.region.stocktaking_enabled):
            return ""
        elif settings.INVENTORY_TAG_MISSING in item.tags.names():
            return _('<div class="small-12 columns label alert">missing</div>')
        elif has_inv_tag:
            return _('<div class="small-12 columns label success">confirmed</div>')
        elif item.user == self.request.user:
            return (
                '<a class="small-6 columns label success" href="{}">{}</a>'
                '<a class="small-6 columns label alert" href="{}">'
                "{}</a>".format(
                    reverse("inventory_tag_confirmation", args=[item.id, "yes"]),
                    _("yes"),
                    reverse("inventory_tag_confirmation", args=[item.id, "no"]),
                    _("no"),
                )
            )
        else:
            return _("<i>Only asset's user can confirm.</i>")

    confirm_ownership.title = _("Do you have it?")


class AssignedLicenceList(Table):
    pass


class AssignedSimcardsList(Table):
    pass


class UserInfoMixin(object):
    user = None

    def get_user(self):
        if not self.user:
            raise NotImplementedError("Please specify user.")
        return self.user

    def get_asset_queryset(self):
        return BackOfficeAsset.objects.filter(
            Q(user=self.get_user()) | Q(owner=self.get_user())
        ).select_related("model", "model__category", "model__manufacturer")

    def get_licence_queryset(self):
        return Licence.objects.filter(users=self.get_user()).select_related("software")

    def get_simcard_queryset(self):
        return SIMCard.objects.filter(user=self.get_user())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: check permission to field or model
        context["asset_list"] = AssetList(
            self.get_asset_queryset(),
            [
                "id",
                "model__category__name",
                "model__manufacturer__name",
                "model__name",
                "sn",
                "barcode",
                "remarks",
                "status",
                "buyout_date",
            ],
            ["user_licence"],
        )
        context["licence_list"] = AssignedLicenceList(
            self.get_licence_queryset(),
            [
                "id",
                "manufacturer",
                "software__name",
                "licence_type",
                "sn",
                "valid_thru",
            ],
        )
        return context


class UserInfoView(UserInfoMixin, RalphDetailView):
    icon = "user"
    name = "user_additional_info"
    label = _("Additional info")
    url_name = "user_additional_info"

    def get_user(self):
        return self.object


class UserTransitionHistoryView(RalphDetailView):
    icon = "history"
    name = "user_transition_history"
    label = _("Transition history")
    url_name = "user_transition_history"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["transitions_history"] = TransitionsHistory.objects.filter(
            Q(kwargs__icontains=self.object.username)
            | Q(kwargs__icontains=self.object.get_full_name())
        ).distinct()
        context["transition_history_in_fieldset"] = False
        return context


@register(RalphUser)
class RalphUserAdmin(UserAdmin, RalphAdmin):
    form = RalphUserChangeForm
    change_views = [UserInfoView, UserTransitionHistoryView]
    readonly_fields = ("api_token_key",)
    fieldsets = (
        (None, {"fields": ("username",)}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                    "regions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Profile"), {"fields": ("country", "city")}),
        (
            _("Job info"),
            {
                "fields": (
                    "company",
                    "profit_center",
                    "cost_center",
                    "department",
                    "manager",
                    "location",
                    "segment",
                    "team",
                )
            },
        ),
    )

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("auth_token")

    def user_change_password(self, request, id, form_url=""):
        # This is backport of django #29686 ticket
        # https://code.djangoproject.com/ticket/29686
        # Django does not pass user object to has_change_permission method
        # And this causes to check only has_view_permission
        user = self.get_object(request, unquote(id))

        if not self.has_change_permission(request, obj=user):
            raise PermissionDenied
        with reversion.create_revision():
            return super().user_change_password(request, id, form_url)


@register(Group)
class RalphGroupAdmin(EditPermissionsFormMixin, GroupAdmin, RalphAdmin):
    readonly_fields = ["ldap_mapping", "users_list"]
    fieldsets = (
        (None, {"fields": ["name", "ldap_mapping", "permissions"]}),
        ("Users", {"fields": ["users_list"]}),
    )

    @cached_property
    def _ldap_groups(self):
        groups = {
            v: k for (k, v) in getattr(settings, "AUTH_LDAP_GROUP_MAPPING", {}).items()
        }
        groups.update(
            {
                v: k
                for (k, v) in getattr(settings, "AUTH_LDAP_NESTED_GROUPS", {}).items()
            }
        )
        return groups

    def ldap_mapping(self, obj):
        return self._ldap_groups.get(obj.name, "-")

    ldap_mapping.short_description = _("LDAP mapping")

    @mark_safe
    def users_list(self, obj):
        users = []
        for u in obj.user_set.order_by("username"):
            users.append(
                '<a href="{}">{}</a>'.format(
                    reverse("admin:accounts_ralphuser_change", args=(u.id,)), str(u)
                )
            )
        return "<br>".join(users)

    users_list.short_description = _("Users list")

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "permissions":
            qs = kwargs.get("queryset", db_field.remote_field.model.objects)
            if qs:
                qs = self._simplify_permissions(qs)
            kwargs["queryset"] = qs
        return super().formfield_for_manytomany(db_field, request=request, **kwargs)


@register(Region)
class RegionAdmin(RalphAdmin):
    search_fields = ["name"]


@register(Team)
class TeamAdmin(RalphAdmin):
    search_fields = ["name"]
