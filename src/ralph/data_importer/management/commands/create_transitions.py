from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from ralph.data_center.models import DataCenterAsset, DataCenterAssetStatus
from ralph.lib.transitions.conf import DEFAULT_ASYNC_TRANSITION_SERVICE_NAME
from ralph.lib.transitions.models import Action, Transition, TransitionModel


class Command(BaseCommand):
    """
    Generate production ready Data Center Asset Transitions
    """

    def handle(self, *args, **options):
        self.create_data_center_asset_transitions()

    @classmethod
    def create_data_center_asset_transitions(cls):
        content_type = ContentType.objects.get_for_model(DataCenterAsset)
        source = [
            DataCenterAssetStatus.new.id,
            DataCenterAssetStatus.used.id,
            DataCenterAssetStatus.free.id,
            DataCenterAssetStatus.damaged.id,
            DataCenterAssetStatus.liquidated.id,
            DataCenterAssetStatus.to_deploy.id,
        ]
        cls.add_transition(
            content_type=content_type,
            name="Deploy",
            source=source,
            actions=[
                "assign_configuration_path",
                "assign_new_hostname",
                "assign_service_env",
                "clean_dhcp",
                "clean_hostname",
                "clean_ipaddresses",
                "cleanup_security_scans",
                "create_dhcp_entries",
                "create_dns_entries",
                "deploy",
                "wait_for_dhcp_servers",
                "wait_for_ping",
            ],
        )

        cls.add_transition(
            name="Change config path",
            actions=["assign_configuration_path"],
            content_type=content_type,
            source=source,
            async_service_name=None,
        )

        cls.add_transition(
            name="Reinstall",
            actions=["deploy", "wait_for_ping"],
            content_type=content_type,
            source=source,
        )

    @classmethod
    def add_transition(
        cls,
        content_type,
        name,
        source,
        actions,
        async_service_name=DEFAULT_ASYNC_TRANSITION_SERVICE_NAME,
        target=0,
    ):
        transition, _ = Transition.objects.get_or_create(
            model=TransitionModel.objects.get(content_type=content_type),
            name=name,
            source=source,
            target=target,
            async_service_name=async_service_name,
        )
        for action in actions:
            transition.actions.add(
                Action.objects.get(name=action, content_type=content_type)
            )
