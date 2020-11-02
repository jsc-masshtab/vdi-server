# -*- coding: utf-8 -*-
import asyncio

from common.database import db


from common.models.vm import Vm
from common.models.pool import Pool
from common.models.controller import Controller
from common.models.auth import (Entity as EntityModel, EntityRoleOwner as EntityRoleOwnerModel)

from common.veil.veil_gino import EntityType


class VmManager:

    def __init__(self):
        self.query_interval = 30

    async def start(self):

        await self._keep_vms_on_task()

    async def _keep_vms_on_task(self):
        """Держим машины вкюченными, если машины находятся в пуле с поднятым флагом keep_vms_on и
        имеют назначенного юзера"""
        while True:

            # get vm info from controllers
            controllers = await Controller.get_objects()

            for controller in controllers:

                # get vms which have users and should be kept on
                ero_query = EntityRoleOwnerModel.select('entity_id').where(EntityRoleOwnerModel.user_id != None)  # noqa

                entity_query = EntityModel.select('entity_uuid').where(
                    (EntityModel.entity_type == EntityType.VM) & (EntityModel.id.in_(ero_query)))

                local_vm_data_list = await db.select([Vm.id]).select_from(Vm.join(Pool)).where(
                    Pool.keep_vms_on & (Pool.controller == controller.id) & (Vm.id.in_(entity_query))).gino.all()
                vm_ids_list = [str(vm_id) for (vm_id, ) in local_vm_data_list]
                # print('!!!vm_ids_list ', vm_ids_list, flush=True)

                # turn them on
                if len(vm_ids_list) > 0:
                    await controller.veil_client.domain(template=0).multi_start(entity_ids=vm_ids_list)

            await asyncio.sleep(self.query_interval)
