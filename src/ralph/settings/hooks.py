import os

from ralph.lib.hooks import hook_name_to_env_name

HOOKS = ("back_office.transition_action.email_context",)
HOOKS_CONFIGURATION = {
    hook: os.environ.get(hook_name_to_env_name(hook), "default") for hook in HOOKS
}
