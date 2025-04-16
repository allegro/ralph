from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import fields, serializers

from ralph.accounts.api_simple import SimpleRalphUserSerializer
from ralph.accounts.models import Team
from ralph.api import RalphAPISerializer
from ralph.api.fields import StrField
from ralph.api.serializers import (
    AdditionalLookupRelatedField,
    RalphAPISaveSerializer,
    ReversionHistoryAPISerializerMixin,
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
    ConfigurationClass,
    ConfigurationModule,
    Environment,
    Manufacturer,
    ManufacturerKind,
    ProfitCenter,
    Service,
    ServiceEnvironment,
)
from ralph.assets.models.components import (
    Disk,
    Ethernet,
    FibreChannelCard,
    Memory,
    Processor,
)
from ralph.lib.custom_fields.api import WithCustomFieldsSerializerMixin
from ralph.licences.api_simple import SimpleBaseObjectLicenceSerializer
from ralph.networks.api_simple import IPAddressSimpleSerializer


class TypeFromContentTypeSerializerMixin(RalphAPISerializer):
    object_type = fields.SerializerMethodField(read_only=True)

    def get_object_type(self, instance):
        return instance.content_type.model


class OwnersFromServiceEnvSerializerMixin(RalphAPISerializer):
    business_owners = SimpleRalphUserSerializer(
        many=True, source="service_env.service.business_owners", required=False
    )
    technical_owners = SimpleRalphUserSerializer(
        many=True, source="service_env.service.technical_owners", required=False
    )


class BusinessSegmentSerializer(RalphAPISerializer):
    class Meta:
        model = BusinessSegment
        fields = "__all__"


class BudgetInfoSerializer(RalphAPISerializer):
    class Meta:
        model = BudgetInfo
        fields = "__all__"


class ProfitCenterSerializer(RalphAPISerializer):
    class Meta:
        model = ProfitCenter
        fields = ("id", "name", "description", "url")
        depth = 1


class EnvironmentSerializer(RalphAPISerializer):
    class Meta:
        model = Environment
        fields = "__all__"


class SaveServiceSerializer(ReversionHistoryAPISerializerMixin, RalphAPISerializer):
    """
    Serializer to save (create or update) services. Environments should be
    passed as a list of ids.

    DRF doesn't work out-of-the-box with many-to-many with through table
    (ex. `ServiceEnvironment`). We're overwriting save mechanism to handle
    this m2m relationship ourself.
    """

    environments = AdditionalLookupRelatedField(
        many=True,
        read_only=False,
        queryset=Environment.objects.all(),
        lookup_fields=["name"],
    )
    business_owners = AdditionalLookupRelatedField(
        many=True,
        read_only=False,
        queryset=get_user_model().objects.all(),
        lookup_fields=["username"],
        style={"base_template": "input.html"},
    )
    technical_owners = AdditionalLookupRelatedField(
        many=True,
        read_only=False,
        queryset=get_user_model().objects.all(),
        lookup_fields=["username"],
        style={"base_template": "input.html"},
    )
    support_team = AdditionalLookupRelatedField(
        read_only=False,
        queryset=Team.objects.all(),
        lookup_fields=["name"],
        required=False,
        allow_null=True,
    )
    profit_center = AdditionalLookupRelatedField(
        read_only=False,
        queryset=ProfitCenter.objects.all(),
        lookup_fields=["name"],
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Service
        fields = "__all__"

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
            ServiceEnvironment.objects.filter(service=instance).values_list(
                "environment_id", flat=True
            )
        )
        # create ServiceEnv for new environments
        for environment in environments:
            if environment.id not in current_environments:
                ServiceEnvironment.objects.create(
                    service=instance, environment=environment
                )

    def create(self, validated_data):
        environments = validated_data.pop("environments", [])
        instance = super().create(validated_data)
        self._save_environments(instance, environments)
        return instance

    def update(self, instance, validated_data):
        environments = validated_data.pop("environments", None)
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
        fields = "__all__"


class ServiceEnvironmentSimpleSerializer(RalphAPISerializer):
    service = serializers.CharField(source="service_name", read_only=True)
    environment = serializers.CharField(source="environment_name", read_only=True)
    service_uid = serializers.CharField(read_only=True)

    class Meta:
        model = ServiceEnvironment
        fields = (
            "id",
            "service",
            "environment",
            "url",
            "service_uid",
        )
        _skip_tags_field = True


class ServiceEnvironmentSerializer(
    TypeFromContentTypeSerializerMixin,
    WithCustomFieldsSerializerMixin,
    RalphAPISerializer,
):
    __str__ = StrField(show_type=True)
    business_owners = SimpleRalphUserSerializer(
        many=True, source="service.business_owners"
    )
    technical_owners = SimpleRalphUserSerializer(
        many=True, source="service.technical_owners"
    )

    class Meta:
        model = ServiceEnvironment
        depth = 1
        exclude = ("content_type", "parent", "service_env")


class ManufacturerSerializer(RalphAPISerializer):
    class Meta:
        model = Manufacturer
        fields = "__all__"


class ManufacturerKindSerializer(RalphAPISerializer):
    class Meta:
        model = ManufacturerKind
        fields = "__all__"


class CategorySerializer(RalphAPISerializer):
    depreciation_rate = serializers.FloatField(source="get_default_depreciation_rate")

    class Meta:
        model = Category
        fields = "__all__"


class AssetModelSerializer(WithCustomFieldsSerializerMixin, RalphAPISerializer):
    category = CategorySerializer()

    class Meta:
        model = AssetModel
        fields = (
            "id",
            "url",
            "custom_fields",
            "configuration_variables",
            "category",
            "name",
            "created",
            "modified",
            "type",
            "power_consumption",
            "height_of_device",
            "cores_count",
            "visualization_layout_front",
            "visualization_layout_back",
            "has_parent",
            "manufacturer",
        )
        depth = 1


class AssetModelSaveSerializer(RalphAPISaveSerializer):
    class Meta:
        model = AssetModel
        fields = "__all__"


class BaseObjectPolymorphicSerializer(
    TypeFromContentTypeSerializerMixin, PolymorphicSerializer, RalphAPISerializer
):
    """
    Serializer for BaseObjects viewset (serialize each model using dedicated
    serializer).
    """

    __str__ = StrField(show_type=True)
    service_env = ServiceEnvironmentSerializer()

    class Meta:
        model = BaseObject
        exclude = ("content_type",)


class AssetHolderSerializer(RalphAPISerializer):
    class Meta:
        model = AssetHolder
        fields = "__all__"


class BaseObjectSimpleSerializer(
    TypeFromContentTypeSerializerMixin,
    WithCustomFieldsSerializerMixin,
    RalphAPISerializer,
):
    __str__ = StrField(show_type=True)

    class Meta:
        model = BaseObject
        exclude = ("content_type",)


class ConfigurationModuleSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = ConfigurationModule
        fields = ("id", "url", "name", "parent", "support_team")


class ConfigurationModuleSerializer(
    WithCustomFieldsSerializerMixin, ConfigurationModuleSimpleSerializer
):
    children_modules = serializers.HyperlinkedRelatedField(
        view_name="configurationmodule-detail",
        many=True,
        read_only=True,
        required=False,
    )

    class Meta(ConfigurationModuleSimpleSerializer.Meta):
        fields = ConfigurationModuleSimpleSerializer.Meta.fields + (
            "children_modules",
            "custom_fields",
        )


class ConfigurationClassSimpleSerializer(RalphAPISerializer):
    module = ConfigurationModuleSimpleSerializer()

    class Meta:
        model = ConfigurationClass
        exclude = ("content_type", "configuration_path", "parent")


# TODO: Is there a better way to make it work since drf 3.5?
del ConfigurationClassSimpleSerializer._declared_fields["tags"]


class ConfigurationClassSerializer(
    TypeFromContentTypeSerializerMixin,
    WithCustomFieldsSerializerMixin,
    RalphAPISerializer,
):
    __str__ = StrField(show_type=True)
    module = ConfigurationModuleSimpleSerializer()

    class Meta:
        model = ConfigurationClass
        exclude = ("content_type", "service_env", "configuration_path")


class BaseObjectSerializer(BaseObjectSimpleSerializer):
    """
    Base class for other serializers inheriting from `BaseObject`.
    """

    service_env = ServiceEnvironmentSimpleSerializer()
    licences = SimpleBaseObjectLicenceSerializer(read_only=True, many=True)
    configuration_path = ConfigurationClassSimpleSerializer()

    class Meta(BaseObjectSimpleSerializer.Meta):
        pass


class AssetSerializer(BaseObjectSerializer):
    class Meta(BaseObjectSerializer.Meta):
        model = Asset


class EthernetSimpleSerializer(RalphAPISerializer):
    ipaddress = IPAddressSimpleSerializer()

    class Meta:
        model = Ethernet
        fields = ("id", "mac", "ipaddress", "url")


class EthernetSerializer(EthernetSimpleSerializer):
    class Meta:
        model = Ethernet
        depth = 1
        fields = "__all__"


class MemorySimpleSerializer(RalphAPISerializer):
    class Meta:
        model = Memory
        fields = ("id", "url", "size", "speed")


class MemorySerializer(MemorySimpleSerializer):
    class Meta:
        depth = 1
        model = Memory
        exclude = ("model",)


class FibreChannelCardSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = FibreChannelCard
        fields = ("id", "url", "firmware_version", "speed", "wwn")


class FibreChannelCardSerializer(FibreChannelCardSimpleSerializer):
    class Meta:
        depth = 1
        model = FibreChannelCard
        exclude = ("model",)


class ProcessorSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = Processor
        fields = ("id", "url", "speed", "cores", "logical_cores")


class ProcessorSerializer(ProcessorSimpleSerializer):
    class Meta:
        depth = 1
        model = Processor
        exclude = ("model",)


class DiskSimpleSerializer(RalphAPISerializer):
    class Meta:
        model = Disk
        fields = (
            "id",
            "url",
            "size",
            "serial_number",
            "slot",
            "firmware_version",
        )


class DiskSerializer(DiskSimpleSerializer):
    class Meta:
        depth = 1
        model = Disk
        exclude = ("model",)


# used by DataCenterAsset and VirtualServer serializers
class NetworkComponentSerializerMixin(OwnersFromServiceEnvSerializerMixin):
    # TODO(xor-xor): ethernet -> ethernets
    ethernet = EthernetSimpleSerializer(many=True, source="ethernet_set")
    ipaddresses = fields.SerializerMethodField()

    def get_ipaddresses(self, instance):
        """
        Return list of ip addresses for passed instance.

        Returns:
            list of ip addresses (as strings)
        """
        # don't use `ipaddresses` property here to make use of
        # `ethernet__ipaddresses` in prefetch related
        ipaddresses = []
        for eth in instance.ethernet_set.all():
            try:
                ipaddresses.append(eth.ipaddress.address)
            except AttributeError:
                pass
        return ipaddresses


# used by DataCenterAsset and VirtualServer serializers
class ComponentSerializerMixin(NetworkComponentSerializerMixin):
    disk = DiskSimpleSerializer(many=True, source="disk_set")
    memory = MemorySimpleSerializer(many=True, source="memory_set")
    processors = ProcessorSimpleSerializer(many=True, source="processor_set")
