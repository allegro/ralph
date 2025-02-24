from ralph.apps import RalphAppConfig


class DeploymentConfig(RalphAppConfig):
    name = "ralph.deployment"
    verbose_name = "Deployment"

    def get_load_modules_when_ready(self):
        return super().get_load_modules_when_ready() + ["deployment"]
