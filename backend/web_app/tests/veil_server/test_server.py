# -*- coding: utf-8 -*-
import json
import ssl
import uuid

from aiohttp import web


class VeilTestServer:

    def __init__(self):
        self.base_url = "/api/"

        self.app = web.Application()

        # ssl
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain("87658490_0.0.0.0.cert",
                                         "87658490_0.0.0.0.key")

        # handlers
        self.app.add_routes(
            [web.get(self.base_url + "domains/{domain_id}/", self.get_domain_info)])
        self.app.add_routes([web.get(self.base_url + "domains/", self.get_domains)])

        self.app.add_routes(
            [web.post(self.base_url + "domains/{domain_id}/start/", self.start_vm)])
        self.app.add_routes(
            [web.post(self.base_url + "domains/{domain_id}/shutdown/", self.shutdown_vm)])

        self.app.add_routes(
            [web.post(self.base_url + "domains/{domain_id}/vdi-prepare/", self.prepare_vm)])

        # Групповые действия
        self.app.add_routes(
            [web.post(self.base_url + "domains/multi-manager/", self.multi_manager)])

        # урлы, чтобы не отключился контроллер
        self.app.add_routes(
            [web.post(self.base_url + "domains/{domain_id}/reboot/", self.start_vm)])
        self.app.add_routes(
            [web.post(self.base_url + "domains/{domain_id}/remove/", self.start_vm)])
        self.app.add_routes([web.post(
            self.base_url + "domains/{domain_id}/set-hostname/", self.start_vm)])

        self.app.add_routes([web.post(self.base_url + "domains/multi-create-domain/",
                                      self.multi_create_domain)])
        self.app.add_routes([web.post(
            self.base_url + "domains/{domain_id}/remote-access/", self.remote_access)])

        self.app.add_routes(
            [web.get(self.base_url + "tasks/{task_id}/", self.get_task_data)])

        self.app.add_routes(
            [web.get(self.base_url + "controllers/check/", self.check_controllers)])
        self.app.add_routes([web.get(self.base_url + "controllers/base-version/",
                                     self.get_base_controller_version)])

        # resources
        self.app.add_routes([web.get(self.base_url + "clusters/", self.get_clusters)])
        self.app.add_routes(
            [web.get(self.base_url + "clusters/{cluster_id}/", self.get_cluster)])

        self.app.add_routes(
            [web.get(self.base_url + "resource_pools/", self.get_resource_pools)])
        self.app.add_routes([web.get(
            self.base_url + "resource_pools/{resource_pool_id}/",
            self.get_resource_pool)])

        self.app.add_routes([web.get(self.base_url + "nodes/", self.get_nodes)])
        self.app.add_routes(
            [web.get(self.base_url + "nodes/{node_id}/", self.get_node)])

        self.app.add_routes(
            [web.get(self.base_url + "data-pools/", self.get_datapools)])
        self.app.add_routes(
            [web.get(self.base_url + "data-pools/{datapool_id}/", self.get_datapool)])

        # tags
        self.app.add_routes([web.get(self.base_url + "tags/", self.get_tags)])
        self.app.add_routes([web.post(self.base_url + "tags/", self.get_tags)])
        self.app.add_routes([web.put(self.base_url + "tags/", self.get_tags)])

        # veil events
        self.app.add_routes([web.get(self.base_url + "events/", self.get_veil_events)])

        # USB
        self.app.add_routes([web.post(self.base_url + "domains/{domain_id}/attach-usb/",
                                      self.attach_usb)])
        self.app.add_routes([web.post(self.base_url + "domains/{domain_id}/detach-usb/",
                                      self.detach_usb)])

        # QEMU guest-exec
        self.app.add_routes([web.post(self.base_url + "domains/{domain_id}/guest-command/",
                                      self.guest_command)])

    def start(self):

        web.run_app(self.app, port=443, ssl_context=self.ssl_context)

    async def get_domain_info(self, request):
        domain_id = request.match_info["domain_id"]

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
            "user_power_state": 3,
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
            "guest_utils": {"veil_state": False, "version": "101.1.0", "hostname": "DESKTOP-LI1VKFH", "ipv4": ["192.168.6.0"], "interfaces": ["Ethernet 5"], "qemu_state": True},
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

        return web.Response(text=json.dumps(res_dict), content_type="application/json")

    async def multi_manager(self, request):
        """Обработчик групповых действий."""
        request_json = await request.json()
        action = request_json['action']
        if action == 'delete':
            res_dict = {
            "_task": {
                "id": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                "verbose_name": "Task",
                "name": "Starting the virtual machine win_test.",
                "progress": 0,
                "status": "IN_PROGRESS",
                "created": "2020-10-29T12:08:18.248553Z",
                "executed": 0,
                "finished_time": None,
                "nodes_user_responses": [
                    {
                        "node_id": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                        "node_response": "None"
                    }
                ],
                "events": [
                    {
                        "id": "79280435-3b14-4374-990b-6831aea1008c",
                        "message": "Task created:  Starting the virtual machine win_test.",
                        "user": "solomin",
                        "created": "2020-10-29T12:08:18.433958Z",
                        "task": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                        "readed": [],
                        "entities": [
                            {
                                "entity_uuid": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                                "entity_class": "domain"
                            },
                            {
                                "entity_uuid": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                                "entity_class": "node"
                            }
                        ],
                        "detail_message": "Task",
                        "permissions": {
                            "mark": True
                        },
                        "type": "info"
                    }
                ],
                "nodes_list": [
                    "cdf10fc6-57f8-436c-a031-78ba3ba1ae40"
                ],
                "user": {
                    "id": 204,
                    "username": "solomin"
                },
                "error_message": "",
                "is_cancellable": True,
                "permissions": {
                    "cancel": True,
                    "release_locks": True,
                    "check": True,
                    "run": True
                },
                "is_multitask": False,
                "parent": None,
                "entities": {
                    "0daf02eb-3172-48a8-b50c-a38b751f9b0b": "domain",
                    "cdf10fc6-57f8-436c-a031-78ba3ba1ae40": "node"
                }
            }
        }
        return web.Response(text=json.dumps(res_dict), content_type="application/json",
                            status=202)

    async def start_vm(self, request):
        domain_id = request.match_info["domain_id"]
        try:
            is_async = request.rel_url.query["async"]
        except KeyError:
            is_async = 0
        if is_async:
            res_dict = {
                "_task": {
                    "id": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                    "verbose_name": "Task",
                    "name": "Starting the virtual machine win_test.",
                    "progress": 0,
                    "status": "IN_PROGRESS",
                    "created": "2020-10-29T12:08:18.248553Z",
                    "executed": 0,
                    "finished_time": None,
                    "nodes_user_responses": [
                        {
                            "node_id": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                            "node_response": "None"
                        }
                    ],
                    "events": [
                        {
                            "id": "79280435-3b14-4374-990b-6831aea1008c",
                            "message": "Task created:  Starting the virtual machine win_test.",
                            "user": "solomin",
                            "created": "2020-10-29T12:08:18.433958Z",
                            "task": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                            "readed": [],
                            "entities": [
                                {
                                    "entity_uuid": domain_id,
                                    "entity_class": "domain"
                                },
                                {
                                    "entity_uuid": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                                    "entity_class": "node"
                                }
                            ],
                            "detail_message": "Task",
                            "permissions": {
                                "mark": True
                            },
                            "type": "info"
                        }
                    ],
                    "nodes_list": [
                        "cdf10fc6-57f8-436c-a031-78ba3ba1ae40"
                    ],
                    "user": {
                        "id": 204,
                        "username": "solomin"
                    },
                    "error_message": "",
                    "is_cancellable": True,
                    "permissions": {
                        "cancel": True,
                        "release_locks": True,
                        "check": True,
                        "run": True
                    },
                    "is_multitask": False,
                    "parent": None,
                    "entities": {
                        domain_id: "domain",
                        "cdf10fc6-57f8-436c-a031-78ba3ba1ae40": "node"
                    }
                }
            }
            return web.Response(text=json.dumps(res_dict), content_type="application/json", status=202)

        else:
            res_dict = {
                "id": domain_id,
                "verbose_name": "solo-static-1",
                "description": "",
                "locked_by": "0a5271bd-0984-4ef2-bfbe-59df6fbefa6e",
                "permissions": [
                    "add_to_ad",
                    "attach_iso",
                    "attach_lun",
                    "attach_mdev",
                    "attach_pci",
                    "attach_usb",
                    "attach_vdisk",
                    "attach_veil_utils_iso",
                    "automated_restore",
                    "available_guest_cmds",
                    "backup",
                    "boot",
                    "boot_free",
                    "change_template",
                    "check_recover",
                    "check_verbose_name",
                    "clone",
                    "cloud_init",
                    "config_restore",
                    "consoles",
                    "controllers",
                    "convert_backup",
                    "convert_from_xml",
                    "cpu_models",
                    "create",
                    "detach_iso",
                    "detach_lun",
                    "detach_mdev",
                    "detach_pci",
                    "detach_usb",
                    "detach_vdisk",
                    "detail_size",
                    "domain_template",
                    "drs_stats",
                    "free_domain_name",
                    "get_choices",
                    "guest_command",
                    "list",
                    "migrate",
                    "migrate_available_nodes",
                    "migrate_available_nodes_several",
                    "migrate_unavailable_nodes",
                    "multi_create_domain",
                    "multi_manager",
                    "os_defaults",
                    "os_types",
                    "os_versions",
                    "prepare",
                    "reboot",
                    "recover",
                    "recover_ready_nodes",
                    "remote_access",
                    "remote_access_white_list",
                    "remove",
                    "resource_limits",
                    "resources",
                    "restore_from_xml",
                    "resume",
                    "retrieve",
                    "rm_from_ad",
                    "safety",
                    "set_active",
                    "set_hostname",
                    "set_mtu",
                    "set_owners",
                    "show_backup",
                    "show_vm_from_xml",
                    "shutdown",
                    "snapshots_info",
                    "snapshots_tree",
                    "sound",
                    "spice",
                    "start",
                    "stats_v2",
                    "suspend",
                    "template",
                    "total_size_domains",
                    "update",
                    "update_actual_size",
                    "update_boot",
                    "update_disastery_options",
                    "update_graphics_password",
                    "update_graphics_settings",
                    "update_ha_options",
                    "video"
                ],
                "status": "ACTIVE",
                "created": "2020-12-02T09:43:42.883639Z",
                "modified": "2020-12-02T13:23:41.304883Z",
                "migrated": None,
                "user_power_state": 3,
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
                    "cpu_priority": 1,
                    "cpu_count_max": 2,
                    "cpu_min_guarantee": 0
                },
                "cpu_type": "Other",
                "memory_count": 2048,
                "memory_pool": None,
                "template": False,
                "os_type": "Windows",
                "os_version": "Microsoft Windows 10 (64-bit)",
                "node": {
                    "id": "73bb1a4b-c7c3-4e1a-a890-bf0763c928f4",
                    "verbose_name": "192.168.11.102"
                },
                "thin": True,
                "cloud_init": False,
                "cloud_init_config": {

                },
                "uptime_on_current_node": {
                    "start_time": 0,
                    "uptime": 0,
                    "system_time": "2020-12-02T13:23:41.327858Z"
                },
                "uptime_total": 0,
                "parent": {
                    "id": "c291f72d-9f06-4789-8ef7-57d24783d7c8",
                    "verbose_name": "win10"
                },
                "resource_pool": {
                    "id": "5a55eee9-4687-48b4-9002-b218eefe29e3",
                    "verbose_name": "Veil default cluster resource pool"
                },
                "ha_enabled": False,
                "ha_autoselect": False,
                "ha_nodepolicy": [

                ],
                "ha_boot_order": 1,
                "ha_retrycount": 5,
                "ha_timeout": 60,
                "ha_options_cluster_sync": True,
                "video": {
                    "type": "cirrus",
                    "vram": 16384,
                    "heads": 1
                },
                "sound": {
                    "codec": "micro",
                    "model": "ich6"
                },
                "graphics_password": "jkgOvOBjeGwlHSa9",
                "features": [

                ],
                "machine": "pc",
                "qemu_args": [

                ],
                "remote_access_port": 5908,
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
                "cluster": "396037a5-b222-41b1-b782-bc0584665a21",
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
                    "ide": 3,
                    "scsi": 0,
                    "sata": 13,
                    "usb": 4
                },
                "current_state": "45868178-7162-45b8-9a7e-c4792d89556d",
                "applied_snapshot": "0b062cd0-6461-4044-8c41-9f551ce85630",
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
                "real_remote_access_port": 50013,
                "consoles": [

                ]
            }
            return web.Response(text=json.dumps(res_dict), content_type="application/json", status=200)

    async def shutdown_vm(self, request):
        domain_id = request.match_info["domain_id"]
        try:
            is_async = request.rel_url.query["async"]
        except KeyError:
            is_async = 0
        if is_async:
            res_dict = {
                "_task": {
                    "id": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                    "verbose_name": "Task",
                    "name": "Starting the virtual machine win_test.",
                    "progress": 0,
                    "status": "IN_PROGRESS",
                    "created": "2020-10-29T12:08:18.248553Z",
                    "executed": 0,
                    "finished_time": None,
                    "nodes_user_responses": [
                        {
                            "node_id": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                            "node_response": "None"
                        }
                    ],
                    "events": [
                        {
                            "id": "79280435-3b14-4374-990b-6831aea1008c",
                            "message": "Task created:  Starting the virtual machine win_test.",
                            "user": "solomin",
                            "created": "2020-10-29T12:08:18.433958Z",
                            "task": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                            "readed": [],
                            "entities": [
                                {
                                    "entity_uuid": domain_id,
                                    "entity_class": "domain"
                                },
                                {
                                    "entity_uuid": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                                    "entity_class": "node"
                                }
                            ],
                            "detail_message": "Task",
                            "permissions": {
                                "mark": True
                            },
                            "type": "info"
                        }
                    ],
                    "nodes_list": [
                        "cdf10fc6-57f8-436c-a031-78ba3ba1ae40"
                    ],
                    "user": {
                        "id": 204,
                        "username": "solomin"
                    },
                    "error_message": "",
                    "is_cancellable": True,
                    "permissions": {
                        "cancel": True,
                        "release_locks": True,
                        "check": True,
                        "run": True
                    },
                    "is_multitask": False,
                    "parent": None,
                    "entities": {
                        domain_id: "domain",
                        "cdf10fc6-57f8-436c-a031-78ba3ba1ae40": "node"
                    }
                }
            }
            return web.Response(text=json.dumps(res_dict), content_type="application/json", status=202)

        else:
            res_dict = {
                "id": domain_id,
                "verbose_name": "solo-static-1",
                "description": "",
                "locked_by": "0a5271bd-0984-4ef2-bfbe-59df6fbefa6e",
                "permissions": [
                    "add_to_ad",
                    "attach_iso",
                    "attach_lun",
                    "attach_mdev",
                    "attach_pci",
                    "attach_usb",
                    "attach_vdisk",
                    "attach_veil_utils_iso",
                    "automated_restore",
                    "available_guest_cmds",
                    "backup",
                    "boot",
                    "boot_free",
                    "change_template",
                    "check_recover",
                    "check_verbose_name",
                    "clone",
                    "cloud_init",
                    "config_restore",
                    "consoles",
                    "controllers",
                    "convert_backup",
                    "convert_from_xml",
                    "cpu_models",
                    "create",
                    "detach_iso",
                    "detach_lun",
                    "detach_mdev",
                    "detach_pci",
                    "detach_usb",
                    "detach_vdisk",
                    "detail_size",
                    "domain_template",
                    "drs_stats",
                    "free_domain_name",
                    "get_choices",
                    "guest_command",
                    "list",
                    "migrate",
                    "migrate_available_nodes",
                    "migrate_available_nodes_several",
                    "migrate_unavailable_nodes",
                    "multi_create_domain",
                    "multi_manager",
                    "os_defaults",
                    "os_types",
                    "os_versions",
                    "prepare",
                    "reboot",
                    "recover",
                    "recover_ready_nodes",
                    "remote_access",
                    "remote_access_white_list",
                    "remove",
                    "resource_limits",
                    "resources",
                    "restore_from_xml",
                    "resume",
                    "retrieve",
                    "rm_from_ad",
                    "safety",
                    "set_active",
                    "set_hostname",
                    "set_mtu",
                    "set_owners",
                    "show_backup",
                    "show_vm_from_xml",
                    "shutdown",
                    "snapshots_info",
                    "snapshots_tree",
                    "sound",
                    "spice",
                    "start",
                    "stats_v2",
                    "suspend",
                    "template",
                    "total_size_domains",
                    "update",
                    "update_actual_size",
                    "update_boot",
                    "update_disastery_options",
                    "update_graphics_password",
                    "update_graphics_settings",
                    "update_ha_options",
                    "video"
                ],
                "status": "ACTIVE",
                "created": "2020-12-02T09:43:42.883639Z",
                "modified": "2020-12-02T13:23:41.304883Z",
                "migrated": None,
                "user_power_state": 3,
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
                    "cpu_priority": 1,
                    "cpu_count_max": 2,
                    "cpu_min_guarantee": 0
                },
                "cpu_type": "Other",
                "memory_count": 2048,
                "memory_pool": None,
                "template": False,
                "os_type": "Windows",
                "os_version": "Microsoft Windows 10 (64-bit)",
                "node": {
                    "id": "73bb1a4b-c7c3-4e1a-a890-bf0763c928f4",
                    "verbose_name": "192.168.11.102"
                },
                "thin": True,
                "cloud_init": False,
                "cloud_init_config": {

                },
                "uptime_on_current_node": {
                    "start_time": 0,
                    "uptime": 0,
                    "system_time": "2020-12-02T13:23:41.327858Z"
                },
                "uptime_total": 0,
                "parent": {
                    "id": "c291f72d-9f06-4789-8ef7-57d24783d7c8",
                    "verbose_name": "win10"
                },
                "resource_pool": {
                    "id": "5a55eee9-4687-48b4-9002-b218eefe29e3",
                    "verbose_name": "Veil default cluster resource pool"
                },
                "ha_enabled": False,
                "ha_autoselect": False,
                "ha_nodepolicy": [

                ],
                "ha_boot_order": 1,
                "ha_retrycount": 5,
                "ha_timeout": 60,
                "ha_options_cluster_sync": True,
                "video": {
                    "type": "cirrus",
                    "vram": 16384,
                    "heads": 1
                },
                "sound": {
                    "codec": "micro",
                    "model": "ich6"
                },
                "graphics_password": "jkgOvOBjeGwlHSa9",
                "features": [

                ],
                "machine": "pc",
                "qemu_args": [

                ],
                "remote_access_port": 5908,
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
                "cluster": "396037a5-b222-41b1-b782-bc0584665a21",
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
                    "ide": 3,
                    "scsi": 0,
                    "sata": 13,
                    "usb": 4
                },
                "current_state": "45868178-7162-45b8-9a7e-c4792d89556d",
                "applied_snapshot": "0b062cd0-6461-4044-8c41-9f551ce85630",
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
                "real_remote_access_port": 50013,
                "consoles": [

                ]
            }
            return web.Response(text=json.dumps(res_dict), content_type="application/json", status=200)

    async def prepare_vm(self, request):
        domain_id = request.match_info["domain_id"]
        res_dict = {
            "_task": {
                "id": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                "verbose_name": "Task",
                "name": "Starting the virtual machine win_test.",
                "progress": 0,
                "status": "IN_PROGRESS",
                "created": "2020-10-29T12:08:18.248553Z",
                "executed": 0,
                "finished_time": None,
                "nodes_user_responses": [
                    {
                        "node_id": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                        "node_response": "None"
                    }
                ],
                "events": [
                    {
                        "id": "79280435-3b14-4374-990b-6831aea1008c",
                        "message": "Task created:  Starting the virtual machine win_test.",
                        "user": "solomin",
                        "created": "2020-10-29T12:08:18.433958Z",
                        "task": "0daf02eb-3172-48a8-b50c-a38b751f9b0b",
                        "readed": [],
                        "entities": [
                            {
                                "entity_uuid": domain_id,
                                "entity_class": "domain"
                            },
                            {
                                "entity_uuid": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                                "entity_class": "node"
                            }
                        ],
                        "detail_message": "Task",
                        "permissions": {
                            "mark": True
                        },
                        "type": "info"
                    }
                ],
                "nodes_list": [
                    "cdf10fc6-57f8-436c-a031-78ba3ba1ae40"
                ],
                "user": {
                    "id": 204,
                    "username": "solomin"
                },
                "error_message": "",
                "is_cancellable": True,
                "permissions": {
                    "cancel": True,
                    "release_locks": True,
                    "check": True,
                    "run": True
                },
                "is_multitask": False,
                "parent": None,
                "entities": {
                    domain_id: "domain",
                    "cdf10fc6-57f8-436c-a031-78ba3ba1ae40": "node"
                }
            }
        }
        return web.Response(text=json.dumps(res_dict), content_type="application/json", status=202)

    async def multi_create_domain(self, request):

        domain_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        res_dict = {
            "entity": domain_id,
            "_task": {
                "id": task_id,
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

        return web.Response(text=json.dumps(res_dict), content_type="application/json", status=202)

    async def remote_access(self, request):
        domain_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        res_dict = {
            "_task": {
                "id": task_id,
                "verbose_name": "Task",
                "name": "remote_access",
                "progress": 0,
                "status": "IN_PROGRESS",
                "created": "2020-10-29T12:08:18.248553Z",
                "executed": 0,
                "finished_time": None,
                "entities": {
                    "cdf10fc6-57f8-436c-a031-78ba3ba1ae40": "node",
                    domain_id: "domain"
                }
            }
        }
        return web.Response(text=json.dumps(res_dict), content_type="application/json", status=202)

    @staticmethod
    async def get_domains(request):

        try:
            vm_ids_string = request.rel_url.query["ids"]
            vm_ids = vm_ids_string.split(",")
        except KeyError:
            vm_ids = ["e00219af-f99a-4615-bd3c-85646be3e1d5"]

        results_list = list()

        i = 0

        for vm_id in vm_ids:
            i += 1
            results_list.append({
                "id": vm_id,
                "memory_count": 4096,
                "verbose_name": "19_10-thin_child-{}".format(i),
                "status": "ACTIVE",
                "cpu_count": 1,
                "vmachine_infs_count": 0,
                "vdisks_count": 0,
                "vfunctions_count": 0,
                "luns_count": 0,
                "user_power_state": 3,
                "memory_pool": None,
                "node": {
                    "id": "73bb1a4b-c7c3-4e1a-a890-bf0763c928f4",
                    "verbose_name": "192.168.11.102"
                },
                "template": False,
                "tags": [

                ],
                "hints": 0,
                "resource_pool": {
                    "id": "5a55eee9-4687-48b4-9002-b218eefe29e3",
                    "verbose_name": "Veil default cluster resource pool"
                },
                "parent": {
                    "id": "589ea6af-03b6-4224-a286-48f0e038ce12",
                    "verbose_name": "19_10"
                }
            }
            )

        res_dict = {
            "count": len(results_list),
            "next": None,
            "previous": None,
            "results": results_list
        }
        return web.Response(text=json.dumps(res_dict), content_type="application/json")

    # /api/tasks/{id}/
    async def get_task_data(self, request):

        task_id = request.match_info["task_id"]
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
        return web.Response(text=json.dumps(res_dict), content_type="application/json")

    async def check_controllers(self, request):
        return web.Response(body=json.dumps(dict()), content_type="application/json")

    async def get_base_controller_version(self, request):
        res_dict = {"version": "4.6.0"}
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_clusters(self, request):
        res_dict = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "cpu_count": 12,
                    "id": "c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e",
                    "memory_count": 32065,
                    "verbose_name": "cluster_115",
                    "nodes_count": 1,
                    "status": "ACTIVE",
                    "datacenter": {
                        "id": "84828205-1fc4-45de-8a4b-632bdaacf342",
                        "verbose_name": "Veil default location"
                    },
                    "built_in": False,
                    "hints": 0,
                    "tags": [

                    ]
                }
            ]
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_cluster(self, request):
        res_dict = {
            "cpu_count": 12,
            "created": "2020-02-14T13:54:23.670400Z",
            "datacenter": {
                "id": "84828205-1fc4-45de-8a4b-632bdaacf342",
                "verbose_name": "Veil default location"
            },
            "description": "",
            "id": "c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e",
            "locked_by": None,
            "memory_count": 32065,
            "modified": "2020-10-16T14:51:34.868561Z",
            "nodes": [
                {
                    "id": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                    "verbose_name": "192.168.11.115"
                }
            ],
            "fencing_type": "",
            "heartbeat_type": "",
            "permissions": {
                "drs": True,
                "ha": True,
                "remove": True,
                "update": True,
                "vdi": True,
                "save_fence_settings": True,
                "tag": True,
                "shutdown_domains": True,
                "set_status": True,
                "quorum": True
            },
            "status": "ACTIVE",
            "verbose_name": "cluster_115",
            "built_in": False,
            "hints": 0,
            "tags": [

            ],
            "entity_type": "cluster",
            "quorum": False,
            "ha_autoselect": False,
            "ha_enabled": False,
            "ha_nodepolicy": [

            ],
            "ha_retrycount": 5,
            "ha_timeout": 60,
            "drs_check_timeout": 180,
            "drs_enabled": False,
            "drs_metrics_strategy": "MEMORY",
            "drs_mode": "SOFT",
            "drs_node_settings": {
                "cpu_hh_level": 85,
                "cpu_hi_level": 80,
                "mem_hh_level": 85,
                "mem_hi_level": 80
            },
            "drs_strategy": "AVERAGE",
            "drs_deviation_limit": 2.0,
            "tag_enabled": False,
            "anti_affinity_enabled": False,
            "vdi": False
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    # "id": "5a55eee9-4687-48b4-9002-b218eefe29e3",
    # "verbose_name": "Veil default cluster resource pool"

    async def get_resource_pools(self, request):
        res_dict = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": "5a55eee9-4687-48b4-9002-b218eefe29e3",
                    "verbose_name": "Veil default cluster resource pool",
                    "hints": 0,
                    "tags": [],
                    "organization": None,
                    "domains_count": 27,
                    "cpu_limit": 0,
                    "memory_limit": 0
                }
            ]
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_resource_pool(self, request):
        res_dict = {
            "id": "5a55eee9-4687-48b4-9002-b218eefe29e3",
            "verbose_name": "Veil default cluster resource pool",
            "description": "",
            "locked_by": None,
            "built_in": True,
            "entity_type": "resourcepool",
            "created": "2020-12-09T12:29:33.128609Z",
            "modified": "2020-12-09T12:29:33.128657Z",
            "hints": 0,
            "tags": [],
            "cluster": {
                "id": "c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e",
                "verbose_name": "cluster_115"
            },
            "cpu_shares": 1024,
            "memory_shares": 1024,
            "cpu_min_guarantee": 0,
            "memory_min_guarantee": 0,
            "cpu_limit": 0,
            "memory_limit": 0,
            "cpu_shares_actual": 1024,
            "memory_shares_actual": 1024,
            "nodes_cpu_count": 288,
            "nodes_memory_count": 385868,
            "domains_cpu_count": 55,
            "domains_memory_count": 70000,
            "domains_cpu_free": 0,
            "domains_memory_free": 0,
            "cpu_min_guarantee_per_domain": 0,
            "memory_min_guarantee_per_domain": 0,
            "cpu_min_guarantee_per_domain_actual": 0,
            "memory_min_guarantee_per_domain_actual": 0,
            "size_limit": 0,
            "permissions": {
                "add_datapools": True,
                "apply": True,
                "attach": True,
                "check_verbose_name": True,
                "create": True,
                "detach": True,
                "detail_size": True,
                "list": True,
                "modify": True,
                "optimal_node": True,
                "remove": True,
                "remove_datapools": True,
                "retrieve": True,
                "transfer_domains": True,
                "update": True,
                "update_actual_size": True
            }
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_nodes(self, request):
        res_dict = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "cpu_count": 24,
                    "id": "39d23118-d37a-454d-a74d-899d1bf2065f",
                    "memory_count": 32021,
                    "verbose_name": "192.168.11.111",
                    "status": "ACTIVE",
                    "management_ip": "192.168.11.111",
                    "domains_count": 0,
                    "domains_on_count": 0,
                    "cluster": {
                        "id": "22411c11-38f4-484b-b9a6-99eef7a04776",
                        "verbose_name": "111_cluster"
                    },
                    "built_in": False,
                    "tags": [
                    ],
                    "hints": 1,
                    "datacenter_name": "Veil default location",
                    "datacenter_id": "84828205-1fc4-45de-8a4b-632bdaacf342",
                    "resource_pools": [
                        {
                            "id": "d6552db1-7db0-4c7b-a5a1-a2dee5346371",
                            "verbose_name": "shumilov"
                        },
                        {
                            "id": "f34cf715-3e49-4074-863b-f3a255d41446",
                            "verbose_name": "111_cluster resource pool"
                        }
                    ]
                }
            ]
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_node(self, request):
        res_dict = {
            "id": "39d23118-d37a-454d-a74d-899d1bf2065f",
            "verbose_name": "192.168.11.111",
            "description": "",
            "locked_by": None,
            "permissions": {
                "update": True,
                "remove": True,
                "fence": True,
                "lsblk": True,
                "discovery": True,
                "discovery_datapool": True,
                "discovery_shared_storage": True,
                "discovery_cluster_storage": True,
                "discovery_zfs_pool": True,
                "update_hw_info": True,
                "save_ipmi_credentials": True,
                "restart_minion": True,
                "ipmi_command": True,
                "set_status": True,
                "swappiness": True,
                "iommu": True,
                "autotest": True,
                "initiator_name": True,
                "save_drs_settings": True,
                "save_fence_settings": True,
                "transfer": True,
                "ksm": True,
                "delete_unknown_domain": True,
                "migrate_domains": True,
                "shutdown_domains": True,
                "start_domains": True,
                "ballooning": True,
                "create_mdev": True,
                "remove_mdev": True,
                "profile": True,
                "ssh_handler": True,
                "service_action": True,
                "backup_os": True
            },
            "status": "ACTIVE",
            "created": "2020-06-19T06:32:33.240526Z",
            "modified": "2020-10-28T10:24:40.156064Z",
            "management_ip": "192.168.11.111",
            "built_in": False,
            "memory_count": 32021,
            "cpu_topology": {
                "cpu_map": {
                    "0": {
                        "cpus": [
                            0,
                            1,
                            2,
                            3,
                            4,
                            5,
                            12,
                            13,
                            14,
                            15,
                            16,
                            17
                        ],
                        "free": "13182",
                        "size": "15916",
                        "distances": "10,21"
                    },
                    "1": {
                        "cpus": [
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            18,
                            19,
                            20,
                            21,
                            22,
                            23
                        ],
                        "free": "10920",
                        "size": "16105",
                        "distances": "21,10"
                    },
                    "all": {}
                },
                "cpu_type": "Intel",
                "cpu_cores": 6,
                "cpu_count": 24,
                "cpu_model": "Haswell-noTSX",
                "proc_info": [
                    {
                        "id": "F2 06 03 00 FF FB EB BF",
                        "family": "Xeon",
                        "status": [
                            "Populated",
                            "Enabled"
                        ],
                        "version": "Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz",
                        "max_speed": "4000 MHz",
                        "manufacturer": "Intel",
                        "thread_count": 12
                    },
                    {
                        "id": "F2 06 03 00 FF FB EB BF",
                        "family": "Xeon",
                        "status": [
                            "Populated",
                            "Enabled"
                        ],
                        "version": "Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz",
                        "max_speed": "4000 MHz",
                        "manufacturer": "Intel",
                        "thread_count": 12
                    }
                ],
                "cpu_mhz_all": 96000,
                "cpu_sockets": 2,
                "cpu_threads": 2,
                "cpu_features": [
                    "abm",
                    "acpi",
                    "aes",
                    "apic",
                    "arat",
                    "avx",
                    "avx2",
                    "bmi1",
                    "bmi2",
                    "clflush",
                    "cmov",
                    "cx16",
                    "cx8",
                    "dca",
                    "de",
                    "ds",
                    "ds_cpl",
                    "dtes64",
                    "erms",
                    "est",
                    "f16c",
                    "fma",
                    "fpu",
                    "fsgsbase",
                    "fxsr",
                    "ht",
                    "invpcid",
                    "invtsc",
                    "lahf_lm",
                    "lm",
                    "mca",
                    "mce",
                    "mmx",
                    "monitor",
                    "movbe",
                    "msr",
                    "mtrr",
                    "nx",
                    "osxsave",
                    "pae",
                    "pat",
                    "pbe",
                    "pcid",
                    "pclmuldq",
                    "pdcm",
                    "pdpe1gb",
                    "pge",
                    "pni",
                    "popcnt",
                    "pse",
                    "pse36",
                    "rdrand",
                    "rdtscp",
                    "sep",
                    "smep",
                    "smx",
                    "ss",
                    "sse",
                    "sse2",
                    "sse4.1",
                    "sse4.2",
                    "ssse3",
                    "syscall",
                    "tm",
                    "tm2",
                    "tsc",
                    "tsc-deadline",
                    "tsc_adjust",
                    "vme",
                    "vmx",
                    "x2apic",
                    "xsave",
                    "xsaveopt",
                    "xtpr"
                ],
                "cpu_numa_nodes": 2,
                "cpu_architecture": "x86_64"
            },
            "domains_cpu_map": {},
            "ipmi_ip": "192.168.11.152",
            "ipmi_username": "admin",
            "fencing_type": "VIRTUAL",
            "heartbeat_type": "KERNEL",
            "node_plus_controller_installation": False,
            "uptime": {
                "uptime": 175914,
                "start_time": "2020-10-26T09:38:08.000000Z",
                "system_time": "2020-10-28T10:30:02.299699Z",
                "timezone": "Europe/Moscow"
            },
            "drs_settings": {
                "cpu_hh_level": 85,
                "cpu_hi_level": 80,
                "mem_hh_level": 85,
                "mem_hi_level": 80,
                "net_hh_level": 85,
                "net_hi_level": 80,
                "disk_hh_level": 85,
                "disk_hi_level": 80
            },
            "cluster": "22411c11-38f4-484b-b9a6-99eef7a04776",
            "cluster_name": "111_cluster",
            "datacenter_name": "Veil default location",
            "datacenter_id": "84828205-1fc4-45de-8a4b-632bdaacf342",
            "ksm_enable": 0,
            "ksm_sleep_time": 20,
            "ksm_pages_to_scan": 100,
            "ksm_merge_across_nodes": 1,
            "hints": 1,
            "tags": [

            ],
            "version": "4.4.0",
            "ballooning": True,
            "entity_type": "node"
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_datapools(self, request):
        res_dict = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": "ba13e5a5-d405-4ea3-bb74-82c139a0638a",
                    "status": "ACTIVE",
                    "verbose_name": "trans",
                    "built_in": False,
                    "free_space": 3402402,
                    "size": 3603492,
                    "used_space": 201090,
                    "shared_storage": {
                        "id": "e7b6266d-eeaf-4728-9946-b6e34b10f2cc",
                        "verbose_name": "14.1_trans"
                    },
                    "cluster_storage": None,
                    "nodes_connected": [
                        {
                            "id": "cdf10fc6-57f8-436c-a031-78ba3ba1ae40",
                            "verbose_name": "192.168.11.115",
                            "connection_status": "SUCCESS"
                        },
                        {
                            "id": "85e68238-8bf6-4f5b-a06c-1926f38df05b",
                            "verbose_name": "192.168.11.110",
                            "connection_status": "FAILED"
                        }
                    ],
                    "iso_count": 0,
                    "file_count": 0,
                    "type": "nfs",
                    "vdisk_count": 1,
                    "zfs_pool": None,
                    "hints": 2,
                    "tags": [

                    ],
                    "resource_pools": [

                    ]
                }
            ]
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_datapool(self, request):
        res_dict = {
            "id": "ba13e5a5-d405-4ea3-bb74-82c139a0638a",
            "verbose_name": "trans",
            "description": "description",
            "locked_by": None,
            "built_in": True,
            "entity_type": "datapool",
            "status": "ACTIVE",
            "created": "2020-09-03T04:25:06.624204Z",
            "modified": "2020-10-28T10:51:46.257530Z",
            "type": "local",
            "options": {
                "path": "/storages/local/default"
            },
            "path": "/storages/local/default",
            "free_space": 3402402,
            "size": 3603492,
            "used_space": 201090,
            "shared_storage": None,
            "cluster_storage": None,
            "nodes_connected": [
                {
                    "id": "0ca1aa55-b1d8-427e-bbf7-9f8ac57db911",
                    "verbose_name": "192.168.11.113",
                    "connection_status": "SUCCESS"
                }
            ],
            "permissions": {
                "update": True,
                "remove": False,
                "unregister": True,
                "clear": True,
                "discover_iso": True,
                "discover_vdisks": True,
                "discover_files": True
            },
            "lun": None,
            "zfs_pool": None,
            "hints": 0,
            "tags": [
            ]
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_tags(self, request):
        res_dict = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "verbose_name": "tag10",
                    "id": "71b2543f-cc35-4f80-9238-bec86c08174f",
                    "colour": "#c0ffee",
                    "ui_entities": []
                },
                {
                    "verbose_name": "newname",
                    "id": "167e50d8-4fbc-4e05-966d-b429e9db9438",
                    "colour": "#ff0000",
                    "ui_entities": []
                }
            ]
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def get_veil_events(self, request):
        res_dict = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": "9863da03-5497-4df1-947e-0ce360631062",
                    "message": "Обновление информации о виртуальной машине broker-test (391bf28f-1757-467a-8c64-589ad9f135a0).",
                    "user": "vdi_emil",
                    "detail_message": "Обновление информации о виртуальной машине broker-test (391bf28f-1757-467a-8c64-589ad9f135a0).",
                    "type": "info",
                    "created": "2021-08-20T10:08:09.761081Z",
                    "task": None,
                    "readed": [],
                    "entities": [
                        {
                            "entity_uuid": "391bf28f-1757-467a-8c64-589ad9f135a0",
                            "entity_class": "domain"
                        }
                    ]
                }
            ]
        }
        return web.Response(body=json.dumps(res_dict), content_type="application/json")

    async def attach_usb(self, request):

        request_json = await request.json()

        res_dict = {
                "tcp_usb_devices": [
                    {
                        "host": request_json["tcp_usb"]["host"],
                        "service": request_json["tcp_usb"]["service"],
                        "uuid": "10b2543f-cc35-4f80-9238-bec86c08174d"
                    }
                ]
        }
        return web.Response(text=json.dumps(res_dict), content_type="application/json", status=200)

    async def detach_usb(self, request):
        # print('!!!detach_usb', flush=True)
        res_dict = {}
        return web.Response(text=json.dumps(res_dict), content_type="application/json", status=202)

    async def guest_command(self, request):
        request_json = await request.json()

        qemu_cmd = request_json["qemu_cmd"]
        fargs = request_json["fargs"]

        res_dict = {}
        if qemu_cmd == "guest-exec":

            # Mock wscript.exe call
            path = fargs.get("path")
            if path == "wscript.exe":
                res_dict = {
                    "guest-exec": {
                        "out-data": """
                            {
                                "farmlist": []
                            }
                        """
                    }
                }

        return web.Response(text=json.dumps(res_dict), content_type="application/json", status=200)


if __name__ == "__main__":
    server = VeilTestServer()
    server.start()
