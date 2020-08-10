# -*- coding: utf-8 -*-
import uuid
import asyncio

from sqlalchemy.dialects.postgresql import UUID
from asyncpg.exceptions import UniqueViolationError
from veil_api_client import DomainConfiguration

from common.database import db
from common.veil.veil_gino import get_list_of_values_from_db, EntityType, VeilModel
from common.veil.veil_errors import BadRequest, VmCreationError, SimpleError
from common.languages import lang_init
from common.log.journal import system_logger

from common.models.auth import Entity as EntityModel, EntityRoleOwner as EntityRoleOwnerModel, User as UserModel


_ = lang_init()


class Vm(VeilModel):
    """
    ACTIONS = ('start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot')
    POWER_STATES = ('unknown', 'power off', 'power on and suspended', 'power on')
    """
    # TODO: положить в таблицу данные о удаленном подключении из ECP
    # TODO: ip address of domain?
    # TODO: port of domain?

    __tablename__ = 'vm'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=255), nullable=False)
    pool_id = db.Column(UUID(), db.ForeignKey('pool.id', ondelete="CASCADE"), unique=False)
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    created_by_vdi = db.Column(db.Boolean(), nullable=False, default=False)
    broken = db.Column(db.Boolean(), nullable=False, default=False)

    @property
    def id_str(self):
        return str(self.id)

    @property
    def entity_type(self):
        return EntityType.VM

    @property
    async def entity_obj(self):
        return await EntityModel.query.where(
            (EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id)).gino.first()

    @property
    def controller_query(self):
        from common.models.controller import Controller as ControllerModel
        from common.models.pool import Pool as PoolModel
        return db.select([ControllerModel.address]).select_from(
            ControllerModel.join(PoolModel.query.where(PoolModel.id == self.pool_id).alias()).alias())

    @property
    async def controller_address(self):
        return await self.controller_query.gino.scalar()

    @property
    async def username(self):
        entity_query = EntityModel.select('id').where((EntityModel.entity_type == EntityType.VM) & (EntityModel.entity_uuid == self.id))
        ero_query = EntityRoleOwnerModel.select('user_id').where(EntityRoleOwnerModel.entity_id == entity_query)
        user_id = await ero_query.gino.scalar()
        user = await UserModel.get(user_id) if user_id else None
        return user.username if user else None

    @property
    async def pool(self):
        """Возвращает объект модели пула."""
        from common.models.pool import Pool as PoolModel
        return await PoolModel.get(self.pool_id)

    @property
    async def controller(self):
        """Возвращает объект модели контроллера."""
        from common.models.controller import Controller as ControllerModel
        vm_pool = await self.pool
        return await ControllerModel.get(vm_pool.controller)

    # ----- ----- ----- ----- ----- ----- -----

    @classmethod
    async def create(cls, pool_id, template_id, verbose_name, id=None,
                     created_by_vdi=False, broken=False):
        await system_logger.debug(_('Create VM {} on VDI DB.').format(verbose_name))
        try:
            vm = await super().create(id=id,
                                      pool_id=pool_id,
                                      template_id=template_id,
                                      verbose_name=verbose_name,
                                      created_by_vdi=created_by_vdi,
                                      broken=broken)
        except Exception as E:
            raise VmCreationError(str(E))

        await system_logger.info(_('VM {} is created').format(verbose_name), entity=vm.entity)

        return vm

    async def soft_delete(self, creator):
        if self.created_by_vdi:
            domain_client = await self.vm_client
            result = await domain_client.remove(full=True, force=True)
            await system_logger.debug(result)
            # controller_address = await self.controller_address
            # if controller_address:
            #     vm_http_client = await VmHttpClient.create(controller_address, self.id)
            #     try:
            #         await vm_http_client.remove_vm()
            #     except HttpError as http_error:
            #         await system_logger.warning(_('Fail to remove VM {} from ECP: ').format(self.verbose_name, http_error))
            await system_logger.debug(_('Vm {} removed from ECP.').format(self.verbose_name))
        status = await super().soft_delete(creator=creator)
        return status

    # TODO: очевидное дублирование однотипного кода. Переселить это все в универсальный метод
    async def add_user(self, user_id, creator):
        entity = await self.entity_obj
        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityRoleOwnerModel.create(entity_id=entity.id, user_id=user_id)
                user = await UserModel.get(user_id)
                await system_logger.info(
                    _('User {} has been included to VM {}').format(user.username, self.verbose_name),
                    user=creator, entity=self.entity)
        except UniqueViolationError:
            raise SimpleError(_('{} already has permission.').format(type(self).__name__), user=creator)
        return ero

    async def remove_users(self, creator, users_list: list):
        entity = EntityModel.select('id').where((EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id))
        # TODO: временное решение. Скорее всего потом права отзываться будут на конкретные сущности
        await system_logger.info(_('VM {} is clear from users').format(self.verbose_name), user=creator, entity=self.entity)
        if not users_list:
            return await EntityRoleOwnerModel.delete.where(EntityRoleOwnerModel.entity_id == entity).gino.status()
        return await EntityRoleOwnerModel.delete.where(
            (EntityRoleOwnerModel.user_id.in_(users_list)) & (EntityRoleOwnerModel.entity_id == entity)).gino.status()

    # @staticmethod
    # async def get_vm_id(pool_id, user_id):
    #     # TODO: deprecated
    #     entity_query = EntityModel.select('entity_uuid').where(
    #         (EntityModel.entity_type == EntityType.VM) & (
    #             EntityModel.id.in_(EntityRoleOwnerModel.select('entity_id').where(EntityRoleOwnerModel.user_id == user_id))))
    #     vm_query = Vm.select('id').where((Vm.id.in_(entity_query)) & (Vm.pool_id == pool_id))
    #     return await vm_query.gino.scalar()

    # @staticmethod
    # async def get_vm(pool_id, user_id):
    #     entity_query = EntityModel.select('entity_uuid').where(
    #         (EntityModel.entity_type == EntityType.VM) & (
    #             EntityModel.id.in_(EntityRoleOwnerModel.select('entity_id').where(EntityRoleOwnerModel.user_id == user_id))))
    #     vm_query = Vm.query.where((Vm.id.in_(entity_query)) & (Vm.pool_id == pool_id))
    #     return await vm_query.gino.first()

    @staticmethod
    async def get_all_vms_ids():
        # TODO: какой-то бесполезный метод
        return await get_list_of_values_from_db(Vm, Vm.id)

    @staticmethod
    async def get_vms_ids_in_pool(pool_id):
        """Get all vm_ids as list of strings"""
        vm_ids_data = await Vm.select('id').where((Vm.pool_id == pool_id)).gino.all()
        vm_ids = [str(vm_id) for (vm_id,) in vm_ids_data]
        return vm_ids

    @staticmethod
    def ready_to_connect(**info) -> bool:
        """Checks parameters indicating availability for connection."""
        # TODO: сейчас не используется?
        power_state = info.get('user_power_state', 0)
        remote_access = info.get('remote_access', False)
        return power_state != 3 or not remote_access

    @staticmethod
    async def copy(verbose_name: str, domain_id: str, datapool_id: str, controller_id,
                   node_id: str, create_thin_clones: bool):
        """Copy existing VM template for new VM create."""
        from common.models.controller import Controller as ControllerModel
        # TODO: мердж сломал перевод на новый клиент

        # client = await VmHttpClient.create(controller_ip, domain_id, verbose_name)
        vm_controller = await ControllerModel.get(controller_id)
        vm_client = vm_controller.veil_client.domain()
        inner_retry_count = 0
        while True:
            inner_retry_count += 1
            try:
                await system_logger.debug(_('Trying to create VM on ECP with verbose_name={}').format(verbose_name))

                # async def copy_vm(self, node_id: str, datapool_id: str, domain_name: str, create_thin_clones: bool):
                #     url = 'http://{}/api/domains/multi-create-domain/?async=1'.format(self.controller_ip)
                #     body = dict(verbose_name=domain_name,
                #                 node=node_id,
                #                 datapool=datapool_id,
                #                 parent=self.vm_id,
                #                 thin=create_thin_clones)
                #     return await self.fetch_with_response(url=url, method='POST', body=body, controller_control=False)
                vm_configuration = DomainConfiguration(verbose_name=verbose_name, node=node_id, datapool=datapool_id,
                                                       parent=domain_id, thin=create_thin_clones)
                response = await vm_client.create(domain_configuration=vm_configuration)
                # response = await client.copy_vm(node_id=node_id,
                #                                 datapool_id=datapool_id,
                #                                 domain_name=verbose_name,
                #                                 create_thin_clones=create_thin_clones)
                await system_logger.debug(_('Request to create VM sent without surprise. Leaving while.'))
                break
            # TODO: задействовать коды ошибок
            # TODO: новые исключения
            # TODO: если брать текст - только англ
            except BadRequest as http_error:
                # TODO: Нужны коды ошибок

                ecp_errors = http_error.errors.get('errors')
                ecp_detail_l = ecp_errors.get('detail') if ecp_errors else None
                ecp_detail = ecp_detail_l[0] if isinstance(ecp_detail_l, list) else None
                await system_logger.warning(_('ECP error: {}').format(ecp_errors))

                if ecp_errors and ecp_detail and ('Недостаточно свободного места в пуле данных' in ecp_detail or 'not enough free space on data pool' in ecp_detail):
                    await system_logger.warning(_('Controller has not free space for creating new VM.'))
                    raise VmCreationError(_('Not enough free space on data pool'))
                elif ecp_errors and ecp_detail and ('passed node is not valid' in ecp_detail or 'Переданный узел не действителен' in ecp_detail):
                    await system_logger.warning(_('Unknown node {}').format(node_id))
                    raise VmCreationError(_('Controller can\t create VM. Unknown node.'))
                elif ecp_errors and ecp_detail and inner_retry_count < 30:
                    # Тут мы предполагаем, что контроллер заблокирован выполнением задачи. Это может быть и не так,
                    # но сейчас нам это не понятно.
                    await system_logger.debug(_('Possibly blocked by active task on ECP. Wait before next try.'))
                    await asyncio.sleep(10)
                else:
                    await system_logger.debug(_('Something went wrong. Interrupt while.'))
                    raise BadRequest(http_error)

            await system_logger.debug(_('Wait one more try'))
            await asyncio.sleep(1)

        response = response.data
        copy_result = dict(id=response['entity'],
                           task_id=response['_task']['id'],
                           verbose_name=verbose_name)
        # await system_logger.debug(copy_result)
        return copy_result

    @staticmethod
    async def remove_vms(vm_ids, creator):
        """Remove given vms"""
        status = None
        for vm_id in vm_ids:
            vm = await Vm.get(vm_id)
            status = await vm.soft_delete(creator=creator)
            await system_logger.info(_('Vm {} removed from pool').format(vm.verbose_name), entity=vm.entity)
        return status

    # @staticmethod
    # async def enable_remote_access(controller_address, vm_id):
    #     vm_http_client = await VmHttpClient.create(controller_address, vm_id)
    #     remote_access_enabled = await vm_http_client.remote_access_enabled()
    #     if not remote_access_enabled:
    #         await vm_http_client.enable_remote_access()

    @staticmethod
    async def enable_remote_accesses(controller_address, vm_ids):
        # TODO: доделать
        # async_tasks = [
        #     Vm.enable_remote_access(controller_address=controller_address, vm_id=vm_id)
        #     for vm_id in vm_ids
        # ]
        # await tornado.gen.multi(async_tasks)
        raise NotImplementedError()

    # @staticmethod
    # async def get_template_os_type(controller_address, template_id):
    #     vm_http_client = await VmHttpClient.create(controller_address, template_id)
    #     domain_info = await vm_http_client.info()
    #     return domain_info['os_type'] if domain_info else None

    # Удаленные действия над ВМ - новый код
    async def action(self, action_name: str, force: bool = False):
        """Пересылает команду управления ВМ на ECP VeiL."""
        # TODO: проверить есть ли вообще такое действие в допустимых?
        vm_controller = await self.controller
        veil_domain = vm_controller.veil_client.domain(domain_id=self.id_str)
        domain_action = getattr(veil_domain, action_name)
        return await domain_action(force=force)

    @property
    async def vm_client(self):
        """Клиент с сущностью domain на ECP VeiL."""
        vm_controller = await self.controller
        return vm_controller.veil_client.domain(domain_id=self.id_str)

    async def start(self):
        """Пересылает start для ВМ на ECP VeiL."""
        return await self.action('start')

    # TODO: reboot
    # TODO: suspend
    # TODO: reset
    # TODO: shutdown
    # TODO: resume
    # TODO: enable_remote_accesses
    # TODO: disable_remote_access

    async def prepare(self):
        """Check that domain remote-access is enabled and domain is powered on."""
        # TODO: 1. Проверить параметры удаленного доступа, если не разрешен - включить и ждать
        # TODO: 2. Послать команду включения и ждать
        # TODO: 3. Ждать активации гостевого агента и появления ip, если на машине RDP?
        # TODO: 4. задание hostname
        # TODO: явная проблема такой логики, что это все заблокирует.
        raise NotImplementedError()
