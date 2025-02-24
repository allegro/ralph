from django.core.management import BaseCommand

from ralph.assets.models import (
    AssetModel,
    Category,
    Manufacturer,
    ObjectModelType
)

DEFAULT_MODEL_CATEGORY = "generic server category"
DEFAULT_MODEL_NAME = "Model A"
DEFAULT_MODEL_MANUFACTURER = "Generic manufacturer"


class Command(BaseCommand):
    """
    Generate a single, production ready server model
    """

    def handle(self, *args, **options):
        model_name = options.get("model_name")
        model_category = options.get("model_category")
        model_manufacturer = options.get("model_manufacturer")
        is_blade = options.get("model_is_blade_server")
        self.create_model(model_name, model_category, model_manufacturer, is_blade)

    def add_arguments(self, parser):
        parser.add_argument(
            "-c",
            "--model-category",
            default=DEFAULT_MODEL_CATEGORY,
            dest="model_category",
            help="Server model category.",
        )
        parser.add_argument(
            "-n",
            "--model-name",
            default=DEFAULT_MODEL_NAME,
            dest="model_name",
            help="Server model.",
        )
        parser.add_argument(
            "-m",
            "--model-manufacturer",
            default=DEFAULT_MODEL_MANUFACTURER,
            dest="model_manufacturer",
            help="Server model manufacturer.",
        )
        parser.add_argument(
            "--model-is-blade-server",
            action="store_true",
            help="If set, model will be marked as blade server.",
        )

    @classmethod
    def create_model(
        cls,
        model_name=DEFAULT_MODEL_NAME,
        model_category=DEFAULT_MODEL_CATEGORY,
        model_manufacturer=DEFAULT_MODEL_MANUFACTURER,
        is_blade=False,
    ):
        category, _ = Category.objects.get_or_create(
            name=model_category, allow_deployment=True
        )
        manufacturer, _ = Manufacturer.objects.get_or_create(name=model_manufacturer)
        AssetModel.objects.get_or_create(
            name=model_name,
            category=category,
            type=ObjectModelType.data_center.id,
            manufacturer=manufacturer,
            has_parent=is_blade,
        )
