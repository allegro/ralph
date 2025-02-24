import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from import_export import widgets

from ralph.assets.models.assets import ServiceEnvironment
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_importer.models import ImportedObjects

logger = logging.getLogger(__name__)


def get_imported_obj(model, old_pk):
    """Get imported object from old primary key.

    :param model: Django model
    :param old_pk: Old primary key

    :return: ContentType, ImportedObjects
    :rtype: tuple
    """
    content_type = ContentType.objects.get_for_model(model)
    imported_obj = ImportedObjects.objects.filter(
        content_type=content_type, old_object_pk=str(old_pk)
    ).first()
    if not imported_obj:
        msg = "Record with pk %s not found for model %s of '%s'"
        logger.warning(msg, str(old_pk), model._meta.model_name, content_type)
    return content_type, imported_obj


class UserWidget(widgets.ForeignKeyWidget):
    """Widget for Ralph User Foreign Key field."""

    def clean(self, value, *args, **kwargs):
        result = None
        if value:
            result, created = get_user_model().objects.get_or_create(
                username=value,
            )
            if created:
                logger.warning("User not found: %s create a new.", value)
        return result

    def render(self, value, obj=None):
        if value:
            return value.username
        return ""


class UserManyToManyWidget(widgets.ManyToManyWidget):
    """Widget for many Ralph Users Foreign Key field."""

    def clean(self, value, *args, **kwargs):
        if not value:
            return get_user_model().objects.none()
        usernames = value.split(self.separator)
        return get_user_model().objects.filter(username__in=usernames)

    def render(self, value, obj=None):
        return self.separator.join([obj.username for obj in value.all()])


class ManyToManyThroughWidget(widgets.ManyToManyWidget):
    """
    Widget for many-to-many relations with through table. This widget accept
    or return list of related models PKs (other-end of through table).
    """

    def __init__(self, through_field, related_model, *args, **kwargs):
        """
        Args:
            model: Django's through model
            related_model: the-other-end model of m2m relation
            through_field: name of field in through model pointing to
                `related_model` (when used together with `ThroughField`, it
                should be the same as `through_to_field_name`)
        """
        self.through_field = through_field
        self.related_model = related_model
        super().__init__(*args, **kwargs)

    def clean(self, value, *args, **kwargs):
        if not value:
            return self.related_model.objects.none()
        return self.related_model.objects.filter(pk__in=value.split(self.separator))

    def render(self, value, obj=None):
        return self.separator.join(
            [str(getattr(obj, self.through_field).pk) for obj in value.all()]
        )


class ExportForeignKeyStrWidget(widgets.Widget):
    def render(self, value, obj=None):
        return str(value)


class ExportManyToManyStrWidget(widgets.ManyToManyWidget):
    def render(self, value, obj=None):
        return self.separator.join([str(obj) for obj in value.all()])


class ExportManyToManyStrTroughWidget(ManyToManyThroughWidget):
    """
    Exporter-equivalent of `ManyToManyThroughWidget` - return str of whole
    object instead of pk.
    """

    def render(self, value, obj=None):
        return self.separator.join(
            [str(getattr(obj, self.through_field)) for obj in value.all()]
        )


class BaseObjectManyToManyWidget(widgets.ManyToManyWidget):
    """Widget for BO/DC base objects."""

    def clean(self, value, *args, **kwargs):
        if not value:
            return self.model.objects.none()
        ids = value.split(self.separator)
        content_types = ContentType.objects.get_for_models(
            BackOfficeAsset,
            DataCenterAsset,
            # TODO: more types
        )
        imported_obj_ids = ImportedObjects.objects.filter(
            content_type__in=content_types.values(), old_object_pk__in=ids
        ).values_list("object_pk", "content_type")
        base_object_ids = []
        for model, content_type in content_types.items():
            model_ids = [i[0] for i in imported_obj_ids if i[1] == content_type.pk]
            base_object_ids.extend(
                model.objects.filter(
                    pk__in=model_ids,
                ).values_list(
                    "baseobject_ptr",
                    flat=True,
                )
            )
        return self.model.objects.filter(pk__in=base_object_ids)


class BaseObjectWidget(widgets.ForeignKeyWidget):
    """Widget for BO/DC base objects."""

    def clean(self, value, *args, **kwargs):
        if not value:
            return None
        result = None
        asset_type, asset_id = value.split("|")  # dc/bo, pk
        models = {"bo": BackOfficeAsset, "dc": DataCenterAsset}
        model = models.get(asset_type.lower())
        if not model:
            return None

        content_type, imported_obj = get_imported_obj(model, asset_id)

        if imported_obj:
            result = model.objects.filter(pk=imported_obj.object_pk).first()

        if result:
            return result.baseobject_ptr
        return None


class ImportedForeignKeyWidget(widgets.ForeignKeyWidget):
    """Widget for ForeignKey fields for which can not define unique."""

    def clean(self, value, *args, **kwargs):
        if settings.MAP_IMPORTED_ID_TO_NEW_ID:
            if value:
                content_type, imported_obj = get_imported_obj(self.model, value)
                if imported_obj:
                    value = imported_obj.object_pk
        return super().clean(value)


class NullStringWidget(widgets.CharWidget):
    def clean(self, value, *args, **kwargs):
        return super().clean(value) or None


class AssetServiceEnvWidget(widgets.ForeignKeyWidget):
    """Widget for AssetServiceEnv Foreign Key field.

    CSV field format Service.name|Environment.name
    """

    def clean(self, value, *args, **kwargs):
        if not value:
            return None
        try:
            if value.isdigit():
                value = ServiceEnvironment.objects.get(pk=value)
            else:
                service, enviroment = value.split("|")
                value = ServiceEnvironment.objects.get(
                    service__name=service, environment__name=enviroment
                )
        except (ValueError, ServiceEnvironment.DoesNotExist):
            value = None
        return value

    def render(self, value, obj=None):
        if value is None:
            return ""
        return "{}|{}".format(value.service.name, value.environment.name)


class AssetServiceUidWidget(widgets.ForeignKeyWidget):
    def clean(self, value, *args, **kwargs):
        if not value:
            return None
        try:
            if value.isdigit():
                value = ServiceEnvironment.objects.get(pk=value)
            else:
                service, enviroment = value.split("|")
                value = ServiceEnvironment.objects.get(
                    service__name=service, environment__name=enviroment
                )
        except (ValueError, ServiceEnvironment.DoesNotExist):
            value = None
        return value

    def render(self, value, obj=None):
        if value is None:
            return ""
        return value.service.uid


class IPManagementWidget(widgets.ManyToManyWidget):
    """
    Widget for IPManagement field during DataCenterAsset import.

    Why ManyToMany?
    The concept is this: use ManyToManyWidget (which are skipped by
    django-import-export until DataCenterAsset is created)
    Explanation:
    When importing `DataCenterAsset` `django-import-export` fails on management
    ip. This because management ip is seperate model which can't be created
    wihtout DataCenterAsset (and DataCenterAsset is the result of importing).
    """

    def clean(self, value, *args, **kwargs):
        return value

    def render(self, value, obj=None):
        return value or ""


class BaseObjectServiceNamesM2MWidget(widgets.ManyToManyWidget):
    def render(self, value, obj=None):
        return self.separator.join(
            [bo.service.name if bo.service else "-" for bo in value.all()]
        )


class PriceAmountWidget(widgets.Widget):
    def render(self, value, obj=None):
        return "{0:.2f}".format(value.amount)


class PriceCurrencyWidget(widgets.Widget):
    def render(self, value, obj=None):
        return str(value.currency)
