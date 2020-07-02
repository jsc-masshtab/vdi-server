# -*- coding: utf-8 -*-
import asyncio

from database import db
from common.veil_errors import HttpError
from vm.models import Vm
from vm.schema import VmState
from vm.veil_client import VmHttpClient
from pool.models import Pool
from auth.models import Entity, EntityRoleOwner, EntityType
from controller.models import Controller


class VmManager:

    def __init__(self):
        self.query_interval = 10

    async def start(self):

        await self._keep_vms_on_task()

    async def _keep_vms_on_task(self):
        """Держим машины вкюченными, если машины находятся в пуле с поднятым флагом keep_vms_on"""
        while True:
            # get vms which have users
            local_vm_data_query = db.select([Vm.id, Pool.keep_vms_on]).select_from(Vm.join(Pool)).where(
                Vm.id.in_(Entity.select('entity_uuid').where((Entity.entity_type == EntityType.VM) & (Entity.id.in_(
                    EntityRoleOwner.select('entity_id').where(EntityRoleOwner.user_id != None))))))  # noqa

            local_vm_data_list = await local_vm_data_query.gino.all()

            # get vm info from controllers
            controllers_addresses = await Controller.get_addresses()

            for controller_address in controllers_addresses:
                vm_http_client = await VmHttpClient.create(controller_address, '')
                try:
                    veil_vm_data_list = await vm_http_client.fetch_vms_list()
                except (HttpError, OSError):
                    continue

                # traverse local_vm_data_list and turn on vms if it's required
                for local_vm_data in local_vm_data_list:
                    (vm_id, keep_vms_on) = local_vm_data

                    # do nothing if keep_vms_on is false
                    if not keep_vms_on:
                        continue

                    # find remote vm data
                    try:
                        remote_vm_data = next(data for data in veil_vm_data_list if data['id'] == str(vm_id))
                    except StopIteration:
                        continue

                    # check if vm is turned off and turn it on
                    if remote_vm_data['user_power_state'] == VmState.OFF:
                        vm_http_client = await VmHttpClient.create(controller_address, vm_id)
                        try:
                            await vm_http_client.send_action(action='start')
                        except (HttpError, OSError):
                            pass

            await asyncio.sleep(self.query_interval)
