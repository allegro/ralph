from ralph.admin import RalphAdmin, register
from ralph.deployment.models import Preboot, PrebootFile


@register(PrebootFile)
class PrebootFileAdmin(RalphAdmin):
    pass


@register(Preboot)
class PrebootAdmin(RalphAdmin):
    pass
