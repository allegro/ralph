from django.test import TestCase

from ralph.assets.models import BaseObject
from ralph.data_importer.widgets import (
    ExportManyToManyStrTroughWidget,
    ManyToManyThroughWidget
)
from ralph.licences.models import BaseObjectLicence
from ralph.licences.tests.factories import (
    DataCenterAssetLicenceFactory,
    LicenceFactory
)


class ManyToManyThroughWidgetTestCase(TestCase):
    def setUp(self):
        self.licence = LicenceFactory()
        DataCenterAssetLicenceFactory.create_batch(3, licence=self.licence)
        self.base_objects_ids = [bo.pk for bo in self.licence.base_objects.all()]
        self.widget = ManyToManyThroughWidget(
            model=BaseObjectLicence,
            related_model=BaseObject,
            through_field="base_object",
        )

    def test_clean(self):
        result = self.widget.clean(",".join(map(str, self.base_objects_ids)))
        self.assertCountEqual(
            result, BaseObject.objects.filter(pk__in=self.base_objects_ids)
        )

    def test_clean_empty_value(self):
        result = self.widget.clean("")
        self.assertCountEqual(result, BaseObject.objects.none())
        self.assertEqual(result.model, BaseObject)

    def test_render(self):
        result = self.widget.render(self.licence.baseobjectlicence_set.all())
        self.assertCountEqual(map(int, result.split(",")), self.base_objects_ids)


class ExportManyToManyStrThroughWidgetTestCase(TestCase):
    def setUp(self):
        self.licence = LicenceFactory()
        DataCenterAssetLicenceFactory.create_batch(3, licence=self.licence)
        self.base_objects_ids = [bo.pk for bo in self.licence.base_objects.all()]
        self.widget = ExportManyToManyStrTroughWidget(
            model=BaseObjectLicence,
            related_model=BaseObject,
            through_field="base_object",
        )

    def test_render(self):
        result = self.widget.render(self.licence.baseobjectlicence_set.all())
        self.assertCountEqual(
            result.split(","),
            [
                str(obj)
                for obj in BaseObject.objects.filter(pk__in=self.base_objects_ids)
            ],
        )
