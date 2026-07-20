from django.apps import AppConfig


class SwitchportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ralph.switchports"

    def ready(self):
        from ralph.switchports import signals  # noqa: F401
