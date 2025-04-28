from ralph.apps import RalphAppConfig


class RalphTests(RalphAppConfig):
    name = "ralph.tests"
    label = "tests"
    default = True
