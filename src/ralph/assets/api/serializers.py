from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from ralph.accounts.api_simple import SimpleRalphUserSerializer
from ralph.accounts.models import Team
from ralph.api import RalphAPISerializer
from ralph.api.fields import StrField
from ralph.api.serializers import (
    AdditionalLookupRelatedField,
    ReversionHistoryAPISerializerMixin
)
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


class SaveServiceSerializer(
    ReversionHistoryAPISerializerMixin,
    RalphAPISerializer
):
    """
    Serializer to save (create or update) services. Environments should be
    passed as a list of ids.

    DRF doesn't work out-of-the-box with many-to-many with through table
    (ex. `ServiceEnvironment`). We're overwriting save mechanism to handle
    this m2m relationship ourself.
    """
    environments = AdditionalLookupRelatedField(
        many=True, read_only=False, queryset=Environment.objects.all(),
        lookup_fields=['name'],
    )
    business_owners = AdditionalLookupRelatedField(
        many=True, read_only=False, queryset=get_user_model().objects.all(),
        lookup_fields=['username'],
    )
    technical_owners = AdditionalLookupRelatedField(
        many=True, read_only=False, queryset=get_user_model().objects.all(),
        lookup_fields=['username'],
    )
    support_team = AdditionalLookupRelatedField(
        read_only=False, queryset=Team.objects.all(), lookup_fields=['name'],
        required=False, allow_null=True,
    )
    profit_center = AdditionalLookupRelatedField(
        read_only=False, queryset=ProfitCenter.objects.all(),
        lookup_fields=['name'], required=False, allow_null=True,
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

    business_owners = SimpleRalphUserSerializer(many=True)
    technical_owners = SimpleRalphUserSerializer(many=True)

    class Meta:
        model = Service
        depth = 1


class ServiceEnvironmentSimpleSerializer(RalphAPISerializer):
    service = serializers.CharField(source='service_name', read_only=True)
    environment = serializers.CharField(
        source='environment_name', read_only=True
    )

    class Meta:
        model = ServiceEnvironment
        fields = ('id', 'service', 'environment', 'url')
        _skip_tags_field = True


class ServiceEnvironmentSerializer(RalphAPISerializer):
    __str__ = StrField(show_type=True)

    class Meta:
        model = ServiceEnvironment
        depth = 1
        exclude = ('content_type', 'parent', 'service_env')


class ManufacturerSerializer(RalphAPISerializer):
    class Meta:
        model = Manufacturer


class CategorySerializer(RalphAPISerializer):

    depreciation_rate = serializers.FloatField(
        source='get_default_depreciation_rate'
    )

    class Meta:
        model = Category


class AssetModelSerializer(RalphAPISerializer):

    category = CategorySerializer()

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
    service_env = ServiceEnvironmentSimpleSerializer()
    licences = SimpleBaseObjectLicenceSerializer(read_only=True, many=True)
    __str__ = StrField(show_type=True)

    class Meta:
        model = BaseObject
        exclude = ('content_type', )


class AssetSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Asset
