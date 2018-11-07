INSTANCE_DELETE = {
    "event_type": "instance.delete.end",
    "payload": {
        "nova_object.data": {
            "architecture": "x86_64",
            "availability_zone": "nova",
            "block_devices": [],
            "created_at": "2012-10-29T13:42:11Z",
            "deleted_at": "2012-10-29T13:42:11Z",
            "display_name": "some-server",
            "display_description": "some-server",
            "fault": None,
            "host": "compute",
            "host_name": "some-server",
            "ip_addresses": [],
            "key_name": "my-key",
            "kernel_id": "",
            "launched_at": "2012-10-29T13:42:11Z",
            "image_uuid": "155d900f-4e14-4e4c-a73d-069cbf4541e6",
            "metadata": {},
            "locked": False,
            "node": "fake-mini",
            "os_type": None,
            "progress": 0,
            "ramdisk_id": "",
            "reservation_id": "r-npxv0e40",
            "state": "deleted",
            "task_state": None,
            "power_state": "pending",
            "tenant_id": "6f70656e737461636b20342065766572",
            "terminated_at": "2012-10-29T13:42:11Z",
            "auto_disk_config": "MANUAL",
            "flavor": {
                "nova_object.name": "FlavorPayload",
                "nova_object.data": {
                    "flavorid": "a22d5517-147c-4147-a0d1-e698df5cd4e3",
                    "name": "test_flavor",
                    "root_gb": 1,
                    "vcpus": 1,
                    "ephemeral_gb": 0,
                    "memory_mb": 512,
                    "disabled": False,
                    "rxtx_factor": 1.0,
                    "extra_specs": {
                        "hw:watchdog_action": "disabled"
                    },
                    "projects": None,
                    "swap": 0,
                    "is_public": True,
                    "vcpu_weight": 0
                },
                "nova_object.version": "1.3",
                "nova_object.namespace": "nova"
            },
            "updated_at": "2012-10-29T13:42:11Z",
            "user_id": "fake",
            "uuid": "178b0921-8f85-4257-88b6-2e743b5a975c"
        },
        "nova_object.name": "InstanceActionPayload",
        "nova_object.namespace": "nova",
        "nova_object.version": "1.5"
    },
    "priority": "INFO",
    "publisher_id": "nova-compute:compute"
}
