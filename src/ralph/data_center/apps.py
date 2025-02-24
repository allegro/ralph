from django.conf import settings

from ralph.apps import RalphAppConfig


class DataCenterConfig(RalphAppConfig):
    name = "ralph.data_center"

    def get_load_modules_when_ready(self):
        if settings.ENABLE_HERMES_INTEGRATION:
            return ["publishers", "subscribers"]
        return []
