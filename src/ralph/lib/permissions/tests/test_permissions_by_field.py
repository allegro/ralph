from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase

from ralph.assets.models.assets import AssetModel
from ralph.assets.models.choices import ObjectModelType
from ralph.lib.permissions.models import get_perm_key


class PermissionsByFieldTestCase(TestCase):

    """TestCase PermissionsByField mixin."""

    @classmethod
    def setUpClass(cls):
        """Setup test models permissions.

        TODO:
            Dont use ralph models here - it should be "abstract"
            http://stackoverflow.com/questions/502916/django-how-to-create-a-model-dynamically-just-for-testing  # noqa
        """
        super().setUpClass()
        cls.asset_model = AssetModel.objects.create(
            type=ObjectModelType.back_office
        )

        permission = Permission.objects.get(
            codename='change_assetmodel_height_of_device_field',
        )
        permission_dc_sn = Permission.objects.get(
            codename='view_datacenterasset_sn_field',
        )
        permission_dc_barcode = Permission.objects.get(
            codename='view_datacenterasset_barcode_field',
        )

        # TODO Change to UserFactory
        cls.super_user = get_user_model().objects.create(
            username='superuser',
            is_superuser=True
        )

        cls.user = get_user_model().objects.create(
            username='user'
        )
        cls.user.user_permissions.add(permission)
        cls.user.user_permissions.add(permission_dc_sn)
        cls.user.user_permissions.add(permission_dc_barcode)
        cls.request_factory = RequestFactory()

    def test_get_perm_key(self):
        """Test get_perm_key function."""
        perm_key = get_perm_key('change', 'category', 'code')
        result_perm_key = 'change_category_code_field'
        self.assertEqual(perm_key, result_perm_key)

    def test_superuser_change_has_access_to_field(self):
        """Test has access to field."""
        self.assertTrue(
            self.asset_model.has_access_to_field(
                'height_of_device',
                self.super_user,
                'change'
            )
        )

    def test_user_change_has_access_to_field(self):
        """Test has access to field."""
        self.assertTrue(
            self.asset_model.has_access_to_field(
                'height_of_device',
                self.user,
                'change'
            )
        )

    def test_view_has_access_to_field(self):
        """Test has access to field."""
        self.assertTrue(
            self.asset_model.has_access_to_field(
                'height_of_device',
                self.user,
                'view'
            )
        )

    def test_superuser_allowed_fields(self):
        """Test allowed fields in permissions model."""
        allowed_fields = set([
            'name', 'type', 'manufacturer', 'category', 'power_consumption',
            'height_of_device', 'cores_count', 'visualization_layout_front',
            'visualization_layout_back', 'has_parent', 'id'
        ])
        fields_list = self.asset_model.allowed_fields(
            self.super_user,
            action='change'
        )
        self.assertEqual(allowed_fields, fields_list)

    def test_user_allowed_fields(self):
        """Test allowed fields in permissions model."""
        fields_list = self.asset_model.allowed_fields(
            self.user,
            action='change'
        )
        self.assertEqual(set(['height_of_device']), fields_list)

    def test_user_not_allowed_fields(self):
        """Test not allowed field in permission model."""
        fields_list = self.asset_model.allowed_fields(
            self.user,
            action='change'
        )
        self.assertNotIn(
            'manufacturer',
            fields_list
        )
