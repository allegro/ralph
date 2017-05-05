from django.conf import settings
from ralph.apps import RalphAppConfig


class AssetsConfig(RalphAppConfig):

    name = 'ralph.assets'

    def get_load_modules_when_ready(self):
        if settings.ENABLE_HERMES_INTEGRATION:
            return ['subscribers']
        return []
