from dj.choices import Choices
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey
from reversion import revisions as reversion

from ralph.accounts.models import RalphUser, Regionalizable
from ralph.assets.models import Category, Manufacturer
from ralph.back_office.models import Warehouse
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.lib.polymorphic.models import PolymorphicQuerySet
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import TransitionWorkflowBaseWithPermissions


_SELECT_USED_ACCESSORY_QUERY = """
    SELECT COALESCE(SUM({assignment_table}.{quantity_column}), 0)
    FROM {assignment_table}
    WHERE {assignment_table}.{accessory_id_column} = {accessory_table}.{id_column} # noqa
"""


class AccessoryUsedFreeManager(models.Manager):
    def get_queryset(self):
        id_column = Accessory.baseobject_ptr.field.column

        user_quantity_field = Accessory.users.through._meta.get_field("quantity")  # noqa
        user_accessory_field = Accessory.users.through._meta.get_field("accessory")  # noqa
        user_count_query = _SELECT_USED_ACCESSORY_QUERY.format(
            assignment_table=Accessory.users.through._meta.db_table,
            quantity_column=user_quantity_field.db_column or user_quantity_field.column,  # noqa
            accessory_id_column=user_accessory_field.db_column or user_accessory_field,  # noqa
            accessory_table=Accessory._meta.db_table,
            id_column=id_column,
        )

        return (
            super()
            .get_queryset()
            .extra(
                select={
                    "user_count": user_count_query,
                }
            )
        )


class AccessoryUsedFreeRelatedObjectsManager(AccessoryUsedFreeManager):
    pass


class AccessoryStatus(Choices):
    _ = Choices.Choice

    new = _("new")
    in_progress = _("in progress")
    lost = _("lost")
    damaged = _("damaged")
    used = _("in use")
    free = _("free")
    return_in_progress = _("return in progress")
    liquidated = _("liquidated")
    reserved = _("reserved")


class Accessory(
    AdminAbsoluteUrlMixin,
    TimeStampMixin,
    Regionalizable,
    models.Model,
    metaclass=TransitionWorkflowBaseWithPermissions,
):
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, blank=True, null=True
    )
    category = TreeForeignKey(
        Category, null=True, related_name="+", on_delete=models.CASCADE
    )
    accessory_name = models.CharField(
        max_length=255, null=False, blank=False, help_text=_("Accessory name")
    )
    product_number = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_("Number of accessories"),
    )
    user = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="AccessoryUser", related_name="+"
    )
    owner = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name="+",
        help_text=_("Accessory owner"),
        on_delete=models.SET_NULL,
    )
    status = TransitionField(
        choices=AccessoryStatus(),
        default=AccessoryStatus.new.id,
        null=False,
        blank=False,
        help_text=_("Accessory status"),
    )
    number_bought = models.IntegerField(verbose_name=_("number of purchased items"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    objects = models.Manager()

    @classmethod
    @transition_action(
        form_fields={
            "restock": {
                "field": forms.IntegerField(
                    label=_("restock"),
                )
            }
        },
    )
    def restock(cls, instances, **kwargs):
        restock = int(kwargs["restock"])
        for instance in instances:
            instance.number_bought += restock

    @classmethod
    @transition_action(
        form_fields={
            "accessory_send": {
                "field": forms.IntegerField(
                    label=_("accessory_send"),
                )
            }
        },
    )
    def accessory_send(cls, instances, **kwargs):
        accessory_send = int(kwargs["accessory_send"])
        for instance in instances:
            instance.number_bought -= accessory_send

    @classmethod
    @transition_action(
        form_fields={
            "user": {
                "field": forms.CharField(label=_("User")),
                "autocomplete_field": "user",
            },
            "quantity": {
                "field": forms.IntegerField(label=_("Quantity")),
            },
        },
    )
    def release_accessories(cls, instances, **kwargs):
        user = get_user_model().objects.get(pk=int(kwargs["user"]))
        quantity = kwargs["quantity"]
        accessory_user, created = AccessoryUser.objects.get_or_create(
            user=user, accessory=instances[0], defaults={"quantity": quantity}
        )
        if not created:
            accessory_user.quantity += quantity
            accessory_user.save()

    polymorphic_objects = PolymorphicQuerySet.as_manager()
    objects_used_free = AccessoryUsedFreeManager()
    objects_used_free_with_related = AccessoryUsedFreeRelatedObjectsManager()

    def __str__(self):
        return "{} x {} - ({})".format(
            self.number_bought,
            self.accessory_name,
            self.product_number,
        )

    @cached_property
    def autocomplete_str(self):
        return "{} ({} free) x {} - ({})".format(
            self.number_bought,
            self.free,
            self.accessory_name,
            self.product_number,
        )

    @cached_property
    def used(self):
        if not self.pk:
            return 0
        try:
            return self.user_count or 0
        except AttributeError:
            users_qs = self.user.through.objects.filter(accessory=self)

            def get_sum(qs):
                return qs.aggregate(sum=Sum("quantity"))["sum"] or 0

            return sum(map(get_sum, [users_qs]))

    used._permission_field = "number_bought"

    @cached_property
    def free(self):
        if not self.pk:
            return 0
        return self.number_bought - self.used

    free._permission_field = "number_bought"


@reversion.register()
class AccessoryUser(models.Model):
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="user", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("accessory", "user")

    def __str__(self):
        return "{} of {} assigned to {}".format(
            self.quantity,
            self.accessory,
            self.user,
        )
