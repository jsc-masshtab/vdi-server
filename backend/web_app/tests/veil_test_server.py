from aiohttp import web
import json
import ssl


class VeilTestServer:

    def __init__(self):
        self.base_url = '/api/'

        self.app = web.Application()

        # handlers
        self.app.add_routes([web.get(self.base_url + 'domains/{domain_id}/', self.get_domain_info)])
        self.app.add_routes([web.post(self.base_url + 'domains/{domain_id}/start/', self.start_vm)])

        self.app.add_routes([web.post(self.base_url + 'domains/multi-create-domain/', self.multi_create_domain)])

        self.app.add_routes([web.get(self.base_url + 'tasks/{task_id}/', self.get_task_data)])

        self.app.add_routes([web.get(self.base_url + 'controllers/check/', self.check_controllers)])
        self.app.add_routes([web.get(self.base_url + 'controllers/base-version/', self.get_base_controller_version)])

        # ssl
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain('/home/ubuntu/job/ssl/87658490_0.0.0.0.cert',
                                         '/home/ubuntu/job/ssl/87658490_0.0.0.0.key')

    def start(self):

        web.run_app(self.app, port=443, ssl_context=self.ssl_context)

    async def get_domain_info(self, request):
        domain_id = request.match_info['domain_id']

        res_dict = {
            "id": domain_id,
            "verbose_name": "alt_linux",
            "description": "",
            "locked_by": None,
            "permissions": {
                "update": True,
                "remove": True,
                "spice": True,
                "update_controllers": True,
                "update_video_device": True,
                "update_sound_device": True,
                "update_boot": True,
                "update_ha_options": True,
                "migrate": True,
                "recover": True,
                "update_disastery_options": True,
                "safety": True,
                "start": True,
                "shutdown": True,
                "suspend": True,
                "reboot": True,
                "resume": True,
                "attach_vdisk": True,
                "detach_vdisk": True,
                "attach_iso": True,
                "detach_iso": True,
                "remote_access": True,
                "snapshots_tree": True,
                "snapshots_info": True,
                "attach_usb": True,
                "detach_usb": True,
                "attach_pci": True,
                "detach_pci": True,
                "prepare": True,
                "attach_mdev": True,
                "detach_mdev": True,
                "rm_from_ad": True,
                "attach_lun": True,
                "detach_lun": True,
                "set_hostname": True,
                "set_owners": True,
                "multi_create_domain": True,
                "add_to_ad": True,
                "clone": True,
                "template": True,
                "free_domain_name": True,
                "update_graphics_settings": True,
                "cloud_init": True,
                "backup": True,
                "show_backup": True,
                "attach_veil_utils_iso": True,
                "automated_restore": True,
                "convert_backup": True,
                "config_restore": True,
                "guest_command": True,
                "consoles": True
            },
            "status": "ACTIVE",
            "created": "2020-10-13T05:05:27.373701Z",
            "modified": "2020-10-26T06:13:38.418647Z",
            "migrated": None,
            "user_power_state": 1,
            "cpu_topology": {
                "cpu_map": {

                },
                "cpu_mode": "default",
                "cpu_cores": 1,
                "cpu_count": 2,
                "cpu_model": "default",
                "cpu_shares": 1024,
                "cpu_sockets": 2,
                "cpu_threads": 1,
                "cpu_priority": 10,
                "cpu_count_max": 2,
                "cpu_min_guarantee": 0
            },
            "cpu_type": "Other",
            "memory_count": 2000,
            "memory_pool": None,
            "template": True,
            "os_type": "Linux",
            "os_version": "Alt Linux 9 (64-bit)",
            "node": {
                "id": "236d318f-d57e-4f1b-9097-93d69f8782dd",
                "verbose_name": "192.168.14.151"
            },
            "thin": False,
            "cloud_init": False,
            "cloud_init_config": {

            },
            "uptime_on_current_node": {
                "start_time": 0,
                "uptime": 0,
                "system_time": "2020-10-27T14:27:46.003375Z"
            },
            "uptime_total": 0,
            "parent": None,
            "resource_pool": {
                "id": "5a55eee9-4687-48b4-9002-b218eefe29e3",
                "verbose_name": "Veil default cluster resource pool"
            },
            "ha_enabled": False,
            "ha_autoselect": False,
            "ha_nodepolicy": [

            ],
            "ha_boot_order": 2,
            "ha_retrycount": 5,
            "ha_timeout": 60,
            "ha_options_cluster_sync": True,
            "video": {
                "type": "virtio",
                "vram": 16384,
                "heads": 1
            },
            "sound": {
                "codec": "micro",
                "model": "ich6"
            },
            "graphics_password": "1",
            "features": [

            ],
            "machine": "pc",
            "qemu_args": [

            ],
            "remote_access_port": 5900,
            "remote_access_allow_all": True,
            "tablet": False,
            "remote_access": True,
            "remote_access_white_list": [

            ],
            "spice_stream": False,
            "clean_count": 1,
            "clean_type": "zero",
            "safety": False,
            "disastery_enabled": False,
            "bootmenu": False,
            "bootmenu_timeout": 3,
            "boot_type": "LegacyMBR",
            "memory_min_guarantee": 0,
            "memory_shares": 1024,
            "memory_limit": 0,
            "tcp_usb_devices": [

            ],
            "owners": [

            ],
            "usb_devices": [

            ],
            "pci_devices": [

            ],
            "mdev_devices": [

            ],
            "os_defaults": {
                "controllers": {
                    "vdisk": {
                        "target_bus": "virtio"
                    },
                    "vmachineinf": {
                        "nic_driver": "virtio"
                    }
                },
                "video": {
                    "type": "virtio"
                },
                "sound": {
                    "model": "ich6",
                    "codec": "micro"
                },
                "os_version": {
                    "linux32": "Other Linux (32-bit)"
                }
            },
            "cluster": "6dd44376-0bf5-46b8-8a23-5a1e6fcfe376",
            "controllers": {
                "ide": [
                    {

                    }
                ],
                "pci": [
                    {
                        "model": "pci-root",
                        "order": 0
                    },
                    {
                        "model": "pci-bridge",
                        "order": 1
                    }
                ],
                "usb": [
                    {
                        "model": "nec-xhci",
                        "order": 0
                    }
                ],
                "sata": [
                    {

                    }
                ],
                "scsi": [

                ]
            },
            "free_slots": {
                "pci": 53,
                "ide": 2,
                "scsi": 0,
                "sata": 14,
                "usb": 4
            },
            "current_state": None,
            "applied_snapshot": None,
            "hints": 0,
            "tags": [

            ],
            "spice_usb_channels": [

            ],
            "start_on_boot": False,
            "guest_utils": {

            },
            "graphics_settings": {
                "mouse_mode": "client",
                "streaming_mode": "filter",
                "jpeg_compression": "auto",
                "zlib_compression": "auto",
                "image_compression": "auto_glz",
                "clipboard_copypaste": "yes",
                "filetransfer_enable": "yes",
                "playback_compression": "on"
            },
            "entity_type": "domain",
            "real_remote_access_port": 50002,
            "consoles": []
        }

        return web.Response(text=json.dumps(res_dict), content_type='application/json')

    async def start_vm(self, request):
        domain_id = request.match_info['domain_id']

        res_dict = {
            "id": domain_id,
            "verbose_name": "verbose_name",
            "description": "",
            "locked_by": "c8f63c34-e40a-4e10-be6a-a181f3d42c39",
            "permissions": {
                "update": True,
                "remove": True,
                "spice": True,
                "update_controllers": True,
                "update_video_device": True,
                "update_sound_device": True,
                "update_boot": True,
                "update_ha_options": True,
                "migrate": True,
                "recover": True,
                "update_disastery_options": True,
                "safety": True,
                "start": True,
                "shutdown": True,
                "suspend": True,
                "reboot": True,
                "resume": True,
                "attach_vdisk": True,
                "detach_vdisk": True,
                "attach_iso": True,
                "detach_iso": True,
                "remote_access": True,
                "snapshots_tree": True,
                "snapshots_info": True,
                "attach_usb": True,
                "detach_usb": True,
                "attach_pci": True,
                "detach_pci": True,
                "prepare": True,
                "attach_mdev": True,
                "detach_mdev": True,
                "rm_from_ad": True,
                "attach_lun": True,
                "detach_lun": True,
                "set_hostname": True,
                "set_owners": True,
                "multi_create_domain": True,
                "add_to_ad": True,
                "clone": True,
                "template": True,
                "free_domain_name": True,
                "update_graphics_settings": True,
                "cloud_init": True,
                "backup": True,
                "show_backup": True,
                "attach_veil_utils_iso": True,
                "automated_restore": True,
                "convert_backup": True,
                "config_restore": True,
                "guest_command": True,
                "consoles": True
            },
            "status": "ACTIVE",
            "created": "2020-10-21T10:01:27.921094Z",
            "modified": "2020-10-27T15:04:36.643284Z",
            "migrated": None,
            "user_power_state": 3,
            "cpu_topology": {
                "cpu_map": {

                },
                "cpu_mode": "host-model",
                "cpu_cores": 1,
                "cpu_count": 2,
                "cpu_model": "default",
                "cpu_shares": 1024,
                "cpu_sockets": 2,
                "cpu_threads": 1,
                "cpu_priority": 10,
                "cpu_count_max": 2,
                "cpu_min_guarantee": 0
            },
            "cpu_type": "Intel",
            "memory_count": 4000,
            "memory_pool": None,
            "template": False,
            "os_type": "Linux",
            "os_version": "Alt Linux 9 (64-bit)",
            "node": {
                "id": "5fa241a4-a9f6-46ec-b55e-fe5307f69737",
                "verbose_name": "192.168.14.155"
            },
            "thin": True,
            "cloud_init": False,
            "cloud_init_config": {

            },
            "uptime_on_current_node": {
                "start_time": 0,
                "uptime": 0,
                "system_time": "2020-10-27T15:04:36.872768Z"
            },
            "uptime_total": 0,
            "parent": {
                "id": "f5b758b0-8b30-455f-b2a3-146bb5debd77",
                "verbose_name": "win10_155_template"
            },
            "resource_pool": {
                "id": "3761d10d-9bbe-430d-9c1f-aac6da6162ca",
                "verbose_name": "veil GRID cluster resource pool"
            },
            "ha_enabled": False,
            "ha_autoselect": False,
            "ha_nodepolicy": [

            ],
            "ha_boot_order": 2,
            "ha_retrycount": 5,
            "ha_timeout": 60,
            "ha_options_cluster_sync": True,
            "video": {
                "type": "virtio",
                "vram": 16384,
                "heads": 1
            },
            "sound": {
                "codec": "micro",
                "model": "ich6"
            },
            "graphics_password": "1",
            "features": [

            ],
            "machine": "pc",
            "qemu_args": [

            ],
            "remote_access_port": 5919,
            "remote_access_allow_all": True,
            "tablet": True,
            "remote_access": True,
            "remote_access_white_list": [

            ],
            "spice_stream": False,
            "clean_count": 1,
            "clean_type": "zero",
            "safety": False,
            "disastery_enabled": False,
            "bootmenu": False,
            "bootmenu_timeout": 3,
            "boot_type": "LegacyMBR",
            "memory_min_guarantee": 0,
            "memory_shares": 1024,
            "memory_limit": 0,
            "tcp_usb_devices": [

            ],
            "owners": [

            ],
            "usb_devices": [

            ],
            "pci_devices": [

            ],
            "mdev_devices": [

            ],
            "os_defaults": {
                "controllers": {
                    "vdisk": {
                        "target_bus": "sata"
                    },
                    "vmachineinf": {
                        "nic_driver": "e1000"
                    }
                },
                "video": {
                    "type": "cirrus"
                },
                "sound": {
                    "model": "ich6",
                    "codec": "micro"
                },
                "os_version": {
                    "windowsun": "Unknown Windows"
                }
            },
            "cluster": "bcae0f80-3cee-465d-976d-674a8bf7bdf1",
            "controllers": {
                "ide": [
                    {

                    }
                ],
                "pci": [
                    {
                        "model": "pci-root",
                        "order": 0
                    },
                    {
                        "model": "pci-bridge",
                        "order": 1
                    }
                ],
                "usb": [
                    {
                        "model": "nec-xhci",
                        "order": 0
                    }
                ],
                "sata": [
                    {

                    }
                ],
                "scsi": [

                ]
            },
            "free_slots": {
                "pci": 54,
                "ide": 2,
                "scsi": 0,
                "sata": 14,
                "usb": 4
            },
            "current_state": "faa1f4fe-d547-4924-8f90-638617abad81",
            "applied_snapshot": "2afc0ddc-7944-46d6-a1eb-14dc1711eaf7",
            "hints": 0,
            "tags": [

            ],
            "spice_usb_channels": [

            ],
            "start_on_boot": False,
            "guest_utils": {

            },
            "graphics_settings": {
                "mouse_mode": "client",
                "streaming_mode": "filter",
                "jpeg_compression": "auto",
                "zlib_compression": "auto",
                "image_compression": "auto_glz",
                "clipboard_copypaste": "yes",
                "filetransfer_enable": "yes",
                "playback_compression": "on"
            },
            "entity_type": "domain",
            "real_remote_access_port": 50010,
            "consoles": [

            ]
        }
        return web.Response(text=json.dumps(res_dict), content_type='application/json')

    async def multi_create_domain(self, request):

        res_dict = {
            "entity": "1ee587ec-74f7-46ba-969c-a975b8e7d8dd",
            "_task": {
                "id": "4abe9150-f1f0-4b88-abe1-c3945b2c8a1c",
                "verbose_name": "verbose_name",
                "name": "name",
                "progress": 0,
                "status": "IN_PROGRESS",
                "created": "2020-10-27T07:23:54.332978Z",
                "executed": 0,
                "finished_time": None,
                "nodes_user_responses": [

                ],
                "events": [
                    {
                        "id": "7446dd84-aa17-46a6-9dfd-9dddf50f37f8",
                        "message": "test_vm",
                        "user": "user",
                        "created": "2020-10-27T07:23:54.520764Z",
                        "task": "4abe9150-f1f0-4b88-abe1-c3945b2c8a1c",
                        "readed": [

                        ],
                        "entities": [
                            {
                                "entity_uuid": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                                "entity_class": "node"
                            },
                            {
                                "entity_uuid": "e1e1324d-993d-408e-a0aa-7259d18df3ff",
                                "entity_class": "domain"
                            }
                        ],
                        "detail_message": "test_vm",
                        "permissions": {
                            "mark": True
                        },
                        "type": "info"
                    }
                ],
                "nodes_list": [

                ],
                "user": {
                    "id": 204,
                    "username": "user"
                },
                "error_message": "",
                "is_cancellable": True,
                "permissions": {
                    "cancel": True,
                    "release_locks": True,
                    "check": True,
                    "run": True
                },
                "is_multitask": True,
                "parent": None,
                "entities": {
                    "cdf10fc6-57f8-436c-a031-78ba3ba1ae40": "node",
                    "e1e1324d-993d-408e-a0aa-7259d18df3ff": "domain"
                }
            }
        }

        return web.Response(text=json.dumps(res_dict), content_type='application/json')

    # /api/tasks/{id}/
    async def get_task_data(self, request):

        task_id = request.match_info['task_id']
        print('get_task_data task_id ', task_id)

        res_dict = {
            "id": task_id,
            "verbose_name": "verbose_name",
            "name": "",
            "progress": 100,
            "status": "SUCCESS",
            "created": "2020-10-27T07:23:54.332978Z",
            "executed": "2.492376",
            "finished_time": "2020-10-27T07:23:56.825354Z",
            "nodes_user_responses": [

            ],
            "events": [
                {
                    "id": "7446dd84-aa17-46a6-9dfd-9dddf50f37f8",
                    "message": "",
                    "user": "user",
                    "created": "2020-10-27T07:23:54.520764Z",
                    "task": task_id,
                    "readed": [

                    ],
                    "entities": [
                        {
                            "entity_uuid": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                            "entity_class": "node"
                        },
                        {
                            "entity_uuid": "e1e1324d-993d-408e-a0aa-7259d18df3ff",
                            "entity_class": "domain"
                        }
                    ],
                    "detail_message": "",
                    "permissions": {
                        "mark": True
                    },
                    "type": "info"
                },
                {
                    "id": "16604663-ef68-4a7b-a0a2-22b78b5cc3c0",
                    "message": "",
                    "user": "user",
                    "created": "2020-10-27T07:23:56.520759Z",
                    "task": task_id,
                    "readed": [

                    ],
                    "entities": [
                        {
                            "entity_uuid": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                            "entity_class": "node"
                        },
                        {
                            "entity_uuid": "e1e1324d-993d-408e-a0aa-7259d18df3ff",
                            "entity_class": "domain"
                        }
                    ],
                    "detail_message": "detail_message",
                    "permissions": {
                        "mark": True
                    },
                    "type": "info"
                }
            ],
            "nodes_list": [

            ],
            "user": {
                "id": 204,
                "username": "user"
            },
            "error_message": "",
            "is_cancellable": False,
            "permissions": {
                "cancel": True,
                "release_locks": True,
                "check": True,
                "run": True
            },
            "is_multitask": True,
            "parent": None,
            "entities": {
                "cdf10fc6-57f8-436c-a031-78ba3ba1ae40": "node",
                "e1e1324d-993d-408e-a0aa-7259d18df3ff": "domain"
            }
        }
        return web.Response(text=json.dumps(res_dict), content_type='application/json')

    async def check_controllers(self, request):
        return web.Response(body=json.dumps(dict()), content_type='application/json')

    async def get_base_controller_version(self, request):
        res_dict = {"version": "4.5.0"}
        return web.Response(body=json.dumps(res_dict), content_type='application/json')


if __name__ == '__main__':
    server = VeilTestServer()
    server.start()
