# -*- coding: utf-8 -*-
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from reversion import revisions as reversion

from ralph.accounts.admin import (
    AssetList,
    AssignedLicenceList,
    AssignedSimcardsList,
    UserInfoMixin
)
from ralph.accounts.helpers import (
    ACCEPTANCE_LOAN_TRANSITION_ID,
    acceptance_transition_exists,
    ACCEPTANCE_TRANSITION_ID,
    get_acceptance_url,
    get_assets_to_accept,
    get_assets_to_accept_loan,
    get_loan_acceptance_url,
    loan_transition_exists
)
from ralph.admin.mixins import RalphBaseTemplateView, RalphTemplateView
from ralph.back_office.models import BackOfficeAsset
from ralph.licences.models import BaseObjectLicence


class UserProfileView(RalphTemplateView):
    template_name = "ralphuser/user_profile.html"


class MyEquipmentAssetList(AssetList):
    def user_licence(self, item):
        licences = BaseObjectLicence.objects.filter(base_object=item.id).select_related(
            "licence", "licence__software"
        )
        if licences:
            result = [
                '&emsp; <i class="fa fa-chevron-right" aria-hidden="true"></i> {} ({})'.format(  # noqa
                    bo_licence.licence.software.name,
                    bo_licence.licence.niw,
                )
                for bo_licence in licences
            ]
            return ["<br />".join(result)]
        else:
            return []


class InventoryTagConfirmationView(RalphBaseTemplateView):
    template_name = "ralphuser/inventory_tag_confirmation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_fields = [
            ("barcode", _("Barcode / Inventory Number")),
            "model__category__name",
            "model__manufacturer__name",
            "model__name",
            ("sn", _("Serial Number")),
        ]

        context["asset_details"] = MyEquipmentAssetList(
            BackOfficeAsset.objects.filter(id=self.kwargs["asset_id"]),
            asset_fields,
            request=self.request,
        )
        return context


class InventoryTagView(View):
    http_method_names = ["post"]

    @staticmethod
    def _add_tags(request, asset, tags):
        asset.tags.add(*tags)
        with reversion.create_revision():
            asset.save()
            reversion.set_user(request.user)
            reversion.set_comment("Added tags {}".format(", ".join(tags)))

    def _post_no(self, request, asset):
        tags = [settings.INVENTORY_TAG_MISSING]
        missing_asset_info = "Please contact person responsible " "for asset management"
        if settings.MISSING_ASSET_REPORT_URL is not None:
            missing_asset_info += "\n" + settings.MISSING_ASSET_REPORT_URL

        self._add_tags(request, asset, tags)
        messages.info(request, _(missing_asset_info))

    def _post_yes(self, request, asset):
        base_tag = settings.INVENTORY_TAG
        if asset.warehouse.stocktaking_tag_suffix != "":
            base_tag = "{prefix}-{warehouse}".format(
                prefix=base_tag,
                warehouse=asset.warehouse.stocktaking_tag_suffix,
            )
        date_tag = None
        if settings.INVENTORY_TAG_APPEND_DATE:
            date_tag = "{base}_{date}".format(
                base=base_tag,
                date=date.today().isoformat(),
            )

        tags = [
            base_tag,
            settings.INVENTORY_TAG_USER,
            date_tag,
        ]

        self._add_tags(request, asset, tags)
        messages.success(request, _("Successfully tagged asset"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["answer"] = kwargs["answer"]
        return context

    def post(self, request, *args, **kwargs):
        asset = get_object_or_404(BackOfficeAsset, id=request.POST["asset_id"])
        if asset.user_id != request.user.id or not (
            asset.warehouse.stocktaking_enabled or asset.region.stocktaking_enabled
        ):
            return HttpResponseForbidden()

        if request.POST["answer"] == "yes":
            self._post_yes(request, asset)
        elif request.POST["answer"] == "no":
            self._post_no(request, asset)

        return HttpResponseRedirect(reverse("current_user_info"))


class _AcceptanceProcessByCurrentUserMixin(object):
    def post(self, request, *args, **kwargs):
        action = request.POST["action"]
        if action == "accept":
            acceptance_url = get_acceptance_url(request.user)
        else:
            acceptance_url = get_loan_acceptance_url(request.user)
        if acceptance_url:
            return HttpResponseRedirect(acceptance_url)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["acceptance_transition_id"] = ACCEPTANCE_TRANSITION_ID
        context["acceptance_transition_exists"] = acceptance_transition_exists()  # noqa: E501
        context["assets_to_accept"] = get_assets_to_accept(self.request.user)
        context["loan_transition_id"] = ACCEPTANCE_LOAN_TRANSITION_ID
        context["loan_transition_exists"] = loan_transition_exists()
        context["assets_to_loan"] = get_assets_to_accept_loan(self.request.user)  # noqa: E501
        return context


class _DummyMixin(object):
    pass


AcceptAssetsForCurrentUserMixin = (
    _AcceptanceProcessByCurrentUserMixin
    if settings.ENABLE_ACCEPT_ASSETS_FOR_CURRENT_USER
    else _DummyMixin
)


class CurrentUserInfoView(
    AcceptAssetsForCurrentUserMixin, UserInfoMixin, RalphBaseTemplateView
):
    template_name = "ralphuser/my_equipment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_equipment_links"] = self.get_links()
        asset_fields = [
            "user",
            ("barcode", _("Barcode / Inventory Number")),
            "model__category__name",
            "model__manufacturer__name",
            "model__name",
            ("sn", _("Serial Number")),
            "invoice_date",
            "status",
        ]

        if settings.MY_EQUIPMENT_SHOW_BUYOUT_DATE:
            asset_fields += ["buyout_date"]

        context["asset_list"] = MyEquipmentAssetList(
            self.get_asset_queryset(),
            asset_fields,
            ["user_licence"],
            request=self.request,
        )

        context["licence_list"] = AssignedLicenceList(
            self.get_licence_queryset(),
            [
                ("niw", _("Inventory Number")),
                "manufacturer",
                "software__name",
                "licence_type",
                "sn",
                "valid_thru",
            ],
            request=self.request,
        )
        context["managing_devices_moved_info"] = settings.MANAGING_DEVICES_MOVED_INFO

        context["simcard_list"] = AssignedSimcardsList(
            self.get_simcard_queryset(),
            [
                ("phone_number", _("Phone Number")),
                ("card_number", _("Card Number")),
                ("pin1", _("PIN 1")),
            ],
            request=self.request,
        )

        return context

    def get_links(self):
        result = []
        links = getattr(settings, "MY_EQUIPMENT_LINKS", [])
        kwargs = {
            "username": self.request.user.username,
        }
        for link in links:
            result.append({"url": link["url"].format(**kwargs), "name": link["name"]})
        return result

    def get_user(self):
        return self.request.user

    def get_asset_queryset(self):
        qs = super().get_asset_queryset()
        return qs.select_related("user")
