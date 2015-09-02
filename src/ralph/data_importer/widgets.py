import logging

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
        content_type=content_type,
        old_object_pk=str(old_pk)
    ).first()

    if not imported_obj:
        msg = (
            "Record with pk {pk} not found for model {model} "
            "of '{content_type}'"
        )
        logger.warning(
            msg.format(
                pk=str(old_pk),
                model=model._meta.model_name,
                content_type=content_type,
            )
        )
    return content_type, imported_obj


class UserWidget(widgets.ForeignKeyWidget):

    """Widget for Ralph User Foreign Key field."""

    def clean(self, value):
        result = None
        if value:
            result, created = get_user_model().objects.get_or_create(
                username=value,
            )
            if created:
                logger.warning(
                    'User not found: {} create a new.'.format(value),
                )
        return result


class UserManyToManyWidget(widgets.ManyToManyWidget):

    """Widget for many Ralph Users Foreign Key field."""

    def clean(self, value):
        if not value:
            return get_user_model().objects.none()
        usernames = value.split(self.separator)
        return get_user_model().objects.filter(username__in=usernames)


class BaseObjectManyToManyWidget(widgets.ManyToManyWidget):

    """Widget for BO/DC base objects."""

    def clean(self, value):
        if not value:
            return self.model.objects.none()
        ids = value.split(self.separator)
        content_types = ContentType.objects.get_for_models(
            BackOfficeAsset,
            DataCenterAsset,
        )
        imported_obj_ids = ImportedObjects.objects.filter(
            content_type__in=content_types.values(),
            old_object_pk__in=ids
        ).values_list('object_pk', 'content_type')
        base_object_ids = []
        for model, content_type in content_types.items():
            model_ids = [
                i[0] for i in imported_obj_ids if i[1] == content_type.pk
            ]
            base_object_ids.extend(
                model.objects.filter(
                    pk__in=model_ids,
                ).values_list(
                    'baseobject_ptr',
                    flat=True,
                )
            )
        return self.model.objects.filter(pk__in=base_object_ids)


class BaseObjectWidget(widgets.ForeignKeyWidget):

    """Widget for BO/DC base objects."""

    def clean(self, value):
        if not value:
            return None
        result = None
        asset_type, asset_id = value.split("|")  # dc/bo, pk
        models = {'bo': BackOfficeAsset, 'dc': DataCenterAsset}
        model = models.get(asset_type.lower())
        if not model:
            return None

        content_type, imported_obj = get_imported_obj(model, asset_id)

        if imported_obj:
            result = model.objects.filter(
                pk=int(imported_obj.object_pk)
            ).first()

        if result:
            return result.baseobject_ptr
        return None


class ImportedForeignKeyWidget(widgets.ForeignKeyWidget):

    """Widget for ForeignKey fields for which can not define unique."""

    def clean(self, value):
        result = None
        if value:
            content_type, imported_obj = get_imported_obj(self.model, value)
            if imported_obj:
                result = self.model.objects.filter(
                    pk=int(imported_obj.object_pk)
                ).first()
        return result


class AssetServiceEnvWidget(widgets.ForeignKeyWidget):

    """Widget for AssetServiceEnv Foreign Key field.

    CSV field format Service.name|Environment.name
    """

    def clean(self, value):
        if not value:
            return None
        try:
            value = value.split("|")  # service, enviroment
            value = ServiceEnvironment.objects.get(
                service__name=value[0],
                environment__name=value[1]
            )
        except ServiceEnvironment.DoesNotExist:
            value = None
        return value

    def render(self, value):
        if value is None:
            return ""
        return "{}|{}".format(
            value.service.name,
            value.environment.name
        )
