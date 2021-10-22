from django.db.migrations.operations.base import Operation


class TransitionActionMigration(Operation):
    """
    Force transition creation or update.
    """
    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass
