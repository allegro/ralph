from django.contrib.admin import AdminSite
from django.test import RequestFactory

from ralph.assets.admin import CategoryAdmin
from ralph.assets.models.assets import AssetModel, Category
from ralph.assets.models.choices import ObjectModelType
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.tests import RalphTestCase


class CategoryAdminTest(RalphTestCase):
    def test_asset_count_includes_assets_from_descendant_categories(self):
        data_center = Category.objects.create(name="data center")
        device = Category.objects.create(name="device", parent=data_center)
        switch = Category.objects.create(
            name="switch ethernet rack",
            parent=device,
        )
        other_category = Category.objects.create(name="other")

        switch_model = AssetModel.objects.create(
            name="switch model",
            type=ObjectModelType.data_center,
            category=switch,
        )
        other_model = AssetModel.objects.create(
            name="other model",
            type=ObjectModelType.data_center,
            category=other_category,
        )
        DataCenterAssetFactory(model=switch_model)
        DataCenterAssetFactory(model=other_model)

        admin = CategoryAdmin(Category, AdminSite())
        request = RequestFactory().get("/")
        categories = admin.get_queryset(request)

        self.assertEqual(admin.count(categories.get(pk=switch.pk)), 1)
        self.assertEqual(admin.count(categories.get(pk=device.pk)), 1)
        self.assertEqual(admin.count(categories.get(pk=data_center.pk)), 1)
        self.assertEqual(admin.count(categories.get(pk=other_category.pk)), 1)
