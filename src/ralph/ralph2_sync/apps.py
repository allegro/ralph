from ralph.apps import RalphAppConfig


class Ralph2SyncConfig(RalphAppConfig):
    name = 'ralph.ralph2_sync'
    verbose_name = 'Ralph2 Sync'

    def get_load_modules_when_ready(self):
        return ['subscribers', 'publishers']
