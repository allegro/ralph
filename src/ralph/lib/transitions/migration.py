from django.db.migrations.operations.base import Operation


class TransitionActionMigration(Operation):
    """
    Force transition related `Action` objects creation or update.
    This is an empty migration used only to trigger `post_migrate` signal.
    """
    def state_forwards(self, app_label, state):
        pass

    def database_forwards(
        self, app_label, schema_editor, from_state, to_state
    ):
        pass

    def database_backwards(
        self, app_label, schema_editor, from_state, to_state
    ):
        pass
