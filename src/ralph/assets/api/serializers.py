from django.db import transaction
from rest_framework import serializers

from ralph.api import RalphAPISerializer
from ralph.api.utils import PolymorphicSerializer
from ralph.assets.models import (
    Asset,
    AssetModel,
    BaseObject,
    BusinessSegment,
    Category,
    Environment,
    Manufacturer,
    ProfitCenter,
    Service,
    ServiceEnvironment
)


class BusinessSegmentSerializer(RalphAPISerializer):
    class Meta:
        model = BusinessSegment


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
        ServiceEnvironment.objects.filter(service=instance).delete()
        ServiceEnvironment.objects.bulk_create([
            ServiceEnvironment(service=instance, environment=env)
            for env in environments
        ])

    def create(self, validated_data):
        environments = validated_data.pop('environments', [])
        instance = super().create(validated_data)
        self._save_environments(instance, environments)
        return instance

    def update(self, instance, validated_data):
        environments = validated_data.pop('environments', [])
        result = super().update(instance, validated_data)
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


class BaseObjectSerializer(RalphAPISerializer):
    """
    Base class for other serializers inheriting from `BaseObject`.
    """
    service_env = ServiceEnvironmentSerializer()

    class Meta:
        model = BaseObject
        exclude = ('content_type', )


class AssetSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Asset
