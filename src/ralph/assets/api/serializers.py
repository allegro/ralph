from django.db import transaction
from rest_framework import serializers

from ralph.api import RalphAPISerializer
from ralph.api.utils import PolymorphicSerializer
from ralph.assets.models import (
    Asset,
    AssetHolder,
    AssetModel,
    BaseObject,
    BudgetInfo,
    BusinessSegment,
    Category,
    Environment,
    Manufacturer,
    ProfitCenter,
    Service,
    ServiceEnvironment
)
from ralph.licences.api_simple import SimpleBaseObjectLicenceSerializer


class BusinessSegmentSerializer(RalphAPISerializer):
    class Meta:
        model = BusinessSegment


class BudgetInfoSerializer(RalphAPISerializer):
    class Meta:
        model = BudgetInfo


class ProfitCenterSerializer(RalphAPISerializer):
    class Meta:
        model = ProfitCenter


class EnvironmentSerializer(RalphAPISerializer):
    class Meta:
        model = Environment


class SaveServiceSerializer(RalphAPISerializer):
    """
    Serializer to save (create or update) services. Environments should be
    passed as a list of ids.

    DRF doesn't work out-of-the-box with many-to-many with through table
    (ex. `ServiceEnvironment`). We're overwriting save mechanism to handle
    this m2m relationship ourself.
    """
    environments = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=Environment.objects.all()
    )

    class Meta:
        model = Service

    @transaction.atomic
    def _save_environments(self, instance, environments):
        """
        Save service-environments many-to-many records.
        """
        # delete ServiceEnv for missing environments
        ServiceEnvironment.objects.filter(service=instance).exclude(
            environment__in=environments
        ).delete()
        current_environments = set(
            ServiceEnvironment.objects.filter(
                service=instance
            ).values_list(
                'environment_id', flat=True
            )
        )
        # create ServiceEnv for new environments
        for environment in environments:
            if environment.id not in current_environments:
                ServiceEnvironment.objects.create(
                    service=instance, environment=environment
                )

    def create(self, validated_data):
        environments = validated_data.pop('environments', [])
        instance = super().create(validated_data)
        self._save_environments(instance, environments)
        return instance

    def update(self, instance, validated_data):
        environments = validated_data.pop('environments', None)
        result = super().update(instance, validated_data)
        if environments is not None:
            self._save_environments(instance, environments)
        return result


class ServiceSerializer(RalphAPISerializer):
    class Meta:
        model = Service
        depth = 1


class ServiceEnvironmentSerializer(RalphAPISerializer):
    class Meta:
        model = ServiceEnvironment
        depth = 1
        exclude = ('content_type', 'parent', 'service_env')


class ManufacturerSerializer(RalphAPISerializer):
    class Meta:
        model = Manufacturer


class CategorySerializer(RalphAPISerializer):
    class Meta:
        model = Category


class AssetModelSerializer(RalphAPISerializer):
    class Meta:
        model = AssetModel


class BaseObjectPolymorphicSerializer(
    PolymorphicSerializer,
    RalphAPISerializer
):
    """
    Serializer for BaseObjects viewset (serialize each model using dedicated
    serializer).
    """
    service_env = ServiceEnvironmentSerializer()

    class Meta:
        model = BaseObject
        exclude = ('content_type',)


class AssetHolderSerializer(RalphAPISerializer):
    class Meta:
        model = AssetHolder


class BaseObjectSerializer(RalphAPISerializer):
    """
    Base class for other serializers inheriting from `BaseObject`.
    """
    service_env = ServiceEnvironmentSerializer()
    licences = SimpleBaseObjectLicenceSerializer(read_only=True, many=True)

    class Meta:
        model = BaseObject
        exclude = ('content_type', )


class AssetSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Asset
