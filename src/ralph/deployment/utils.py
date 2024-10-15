from urllib.parse import urljoin

from django.conf import settings
from django.template import Context, Template
from django.urls import reverse


def _render_configuration(configuration, deployment, disable_reverse=False):
    def url(name, kwargs):
        if disable_reverse:
            return "{}({})".format(
                name, ", ".join([str(value) for value in kwargs.values()])
            )
        return reverse(name, kwargs=kwargs)

    template = Template(configuration)
    ralph_instance = settings.RALPH_INSTANCE
    ethernet = deployment.params.get("create_dhcp_entries__ethernet")
    context = Context(
        {
            "configuration_path": str(deployment.obj.configuration_path),
            "configuration_class_name": (
                deployment.obj.configuration_path.class_name
                if deployment.obj.configuration_path
                else None
            ),
            "configuration_module": (
                deployment.obj.configuration_path.module.name
                if deployment.obj.configuration_path
                else None
            ),
            "ralph_instance": ralph_instance,
            "deployment_id": deployment.id,
            "deployment_base": urljoin(
                ralph_instance,
                url("deployment_base", kwargs={"deployment_id": deployment.id}),
            ),
            "kickstart": urljoin(
                ralph_instance,
                url(
                    "deployment_config",
                    kwargs={
                        "deployment_id": deployment.id,
                        "config_type": "kickstart",
                    },
                ),
            ),
            "preseed": urljoin(
                ralph_instance,
                url(
                    "deployment_config",
                    kwargs={
                        "deployment_id": deployment.id,
                        "config_type": "preseed",
                    },
                ),
            ),
            "script": urljoin(
                ralph_instance,
                url(
                    "deployment_config",
                    kwargs={
                        "deployment_id": deployment.id,
                        "config_type": "script",
                    },
                ),
            ),
            "meta_data": urljoin(
                ralph_instance,
                url(
                    "deployment_config",
                    kwargs={
                        "deployment_id": deployment.id,
                        "config_type": "meta-data",
                    },
                ),
            ),
            "user_data": urljoin(
                ralph_instance,
                url(
                    "deployment_config",
                    kwargs={
                        "deployment_id": deployment.id,
                        "config_type": "user-data",
                    },
                ),
            ),
            "initrd": urljoin(
                ralph_instance,
                url(
                    "deployment_files",
                    kwargs={"deployment_id": deployment.id, "file_type": "initrd"},
                ),
            ),
            "kernel": urljoin(
                ralph_instance,
                url(
                    "deployment_files",
                    kwargs={"deployment_id": deployment.id, "file_type": "kernel"},
                ),
            ),
            "netboot": urljoin(
                ralph_instance,
                url(
                    "deployment_files",
                    kwargs={"deployment_id": deployment.id, "file_type": "netboot"},
                ),
            ),
            "dc": deployment.obj.rack.server_room.data_center.name,
            "domain": (
                deployment.obj.network_environment.domain
                if deployment.obj.network_environment
                else None
            ),
            "hostname": deployment.obj.hostname,
            "service_env": str(deployment.obj.service_env),
            "service_uid": (
                deployment.obj.service_env.service.uid
                if deployment.obj.service_env
                else None
            ),
            "done_url": urljoin(
                ralph_instance,
                url("deployment_done", kwargs={"deployment_id": deployment.id}),
            ),
            "mac": ethernet.mac if ethernet else None,
        }
    )
    return template.render(context)
