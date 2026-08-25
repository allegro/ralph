from importlib import import_module

from ddt import data, ddt
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase

from ralph.accounts.models import Region
from ralph.admin.sites import ralph_site
from ralph.admin.tests.tests_views import EXCLUDE_ADD_VIEW, EXCLUDE_MODELS, FACTORY_MAP
from ralph.tests.factories import UserFactory


REGISTERED_MODEL_PATHS = {
    "{}.{}".format(model.__module__, model.__name__) for model in ralph_site._registry
}
ADMIN_FORM_MODELS = sorted(
    model_path
    for model_path in REGISTERED_MODEL_PATHS - set(EXCLUDE_MODELS)
    if model_path.startswith("ralph.")
)


FIELD_PERMISSION_SCENARIOS = (
    ("full", "admin_user"),
    ("readonly", "readonly_user"),
    ("none", "no_field_permissions_user"),
)


@ddt
class AdminFormRenderingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserFactory(is_staff=True, is_superuser=True)
        cls.readonly_user = UserFactory(is_staff=True)
        cls.no_field_permissions_user = UserFactory(is_staff=True)

        permissions = list(Permission.objects.all())
        cls.readonly_user.user_permissions.set(
            permission
            for permission in permissions
            if not (
                permission.codename.startswith("change_")
                and permission.codename.endswith("_field")
            )
        )
        cls.no_field_permissions_user.user_permissions.set(
            permission for permission in permissions if not permission.codename.endswith("_field")
        )

    def setUp(self):
        self.request = RequestFactory().get("/")
        self.request.session = {}
        ContentType.objects.get_for_models(*ralph_site._registry.keys())

    @data(*ADMIN_FORM_MODELS)
    def test_admin_forms_render_for_field_permission_scenarios(self, model_path):
        module_path, model_name = model_path.rsplit(".", 1)
        model = getattr(import_module(module_path), model_name)
        model_admin = ralph_site._registry[model]

        factory_path = FACTORY_MAP[model_path]
        factory_module_path, factory_name = factory_path.rsplit(".", 1)
        factory = getattr(import_module(factory_module_path), factory_name)
        obj = factory()
        self.assertIsNotNone(obj)

        regions = Region.objects.all()
        self.readonly_user.regions.add(*regions)
        self.no_field_permissions_user.regions.add(*regions)

        for scenario, user_attribute in FIELD_PERMISSION_SCENARIOS:
            with self.subTest(field_permissions=scenario):
                self.request.user = getattr(self, user_attribute)
                if model_path not in EXCLUDE_ADD_VIEW:
                    add_response = model_admin.changeform_view(
                        self.request,
                        object_id=None,
                    )
                    add_response.render()
                    self.assertEqual(add_response.status_code, 200)

                change_response = model_admin.changeform_view(
                    self.request,
                    object_id=str(obj.pk),
                )
                change_response.render()
                self.assertEqual(change_response.status_code, 200)
