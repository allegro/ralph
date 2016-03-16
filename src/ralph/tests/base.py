from django.test import TestCase


class RalphTestCase(TestCase):
    def refresh_objects_from_db(self, *objects):
        for obj in objects:
            obj.refresh_from_db()
