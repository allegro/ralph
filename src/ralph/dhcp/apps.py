from ralph.apps import RalphAppConfig


class DHCPConfig(RalphAppConfig):
    name = 'ralph.dhcp'
    verbose_name = 'DHCP'

    def get_load_modules_when_ready(self):
        return super().get_load_modules_when_ready() + ['deployment']
