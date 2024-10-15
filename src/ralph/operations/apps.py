from ralph.apps import RalphAppConfig


class RalphOperationsConfig(RalphAppConfig):
    name = "ralph.operations"
    label = "operations"
    verbose_name = "Ralph Operations"

    def ready(self):
        from ralph.operations.changemanagement.subscribtions import (  # noqa
            receive_chm_event,
        )

        super().ready()
