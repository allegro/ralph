from django.conf import settings

from ralph.apps import RalphAppConfig


class Domains(RalphAppConfig):
    name = "ralph.domains"

    def get_load_modules_when_ready(self):
        if settings.ENABLE_HERMES_INTEGRATION:
            return ["publishers"]
        return []
