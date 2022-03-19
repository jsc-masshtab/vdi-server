import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';



@Injectable()
export class PoolDetailsService {

    constructor(private service: Apollo) { }

    public orderingVms: any = {
        spin: true,
        nameSort: undefined
    };

    public orderingUsers: any = {
        spin: true,
        nameSort: undefined
    };

    public orderingGroups: any = {
        spin: true,
        nameSort: undefined
    };

    public removePool(pool_id: number,  full: boolean) {
        return this.service.mutate<any>({
            mutation: gql`
                        mutation pools($pool_id: UUID, $full: Boolean) {
                            removePool(pool_id: $pool_id, full: $full) {
                                ok
                            }
                        }
            `,
            variables: {
                method: 'POST',
                pool_id,
                full
            }
        });
    }

    public clearPool(data) {
        return this.service.mutate<any>({
            mutation: gql`
                        mutation pools($pool_id: UUID) {
                            clearPool(pool_id: $pool_id) {
                                ok
                            }
                        }
            `,
            variables: {
                method: 'POST',
                ...data,
            }
        });
    }

    public getPool(pool_id: string | number, type: string): QueryRef<any, any> {

        if (type === 'automated' || type === 'guest') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: ShortString, $ordering_vms: ShortString, $ordering_users: ShortString, $ordering_groups: ShortString) {
                                pool(pool_id: $pool_id) {
                                    pool_id
                                    verbose_name
                                    pool_type
                                    vms(ordering: $ordering_vms) {
                                        id
                                        verbose_name
                                        user {
                                            username
                                        }
                                        user_power_state
                                        node {
                                            id
                                            verbose_name
                                        }
                                        qemu_state
                                        assigned_users {
                                          username
                                        }
                                        status
                                        parent_name
                                    }
                                    controller {
                                        id
                                        address
                                        verbose_name
                                    }
                                    initial_size
                                    reserve_size
                                    total_size
                                    increase_step
                                    vm_disconnect_action_timeout
                                    vm_name_template
                                    ad_ou
                                    users(ordering: $ordering_users) {
                                        id
                                        username
                                    }
                                    resource_pool {
                                        verbose_name
                                    }
                                    datapool {
                                        verbose_name
                                    }
                                    template {
                                        verbose_name
                                    }
                                    create_thin_clones
                                    enable_vms_remote_access
                                    start_vms
                                    set_vms_hostnames
                                    include_vms_in_ad
                                    keep_vms_on
                                    free_vm_from_user
                                    assigned_groups(ordering: $ordering_groups) {
                                        id
                                        verbose_name
                                    }
                                    possible_groups{
                                        id
                                        verbose_name
                                    }
                                    assigned_connection_types
                                    status
                                    vm_action_upon_user_disconnect
                                    vm_disconnect_action_timeout
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id,
                    ordering_vms: this.orderingVms.nameSort,
                    ordering_users: this.orderingUsers.nameSort,
                    ordering_groups: this.orderingGroups.nameSort
                }
            });
        }

        if (type === 'static' || type === 'rds') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: ShortString, $ordering_vms: ShortString, $ordering_users: ShortString, $ordering_groups: ShortString) {
                                pool(pool_id: $pool_id) {
                                    verbose_name
                                    pool_type
                                    vms(ordering: $ordering_vms) {
                                        verbose_name
                                        id
                                        user {
                                            username
                                        }
                                        user_power_state
                                        node {
                                            id
                                            verbose_name
                                        }
                                        qemu_state
                                        status
                                        assigned_users {
                                            id
                                            username
                                        }
                                        parent_name
                                        controller {
                                            id
                                        }
                                    }
                                    controller {
                                        id
                                        address
                                        verbose_name
                                    }
                                    resource_pool_id
                                    users(ordering: $ordering_users) {
                                        id
                                        username
                                    }
                                    resource_pool {
                                        verbose_name
                                    }
                                    assigned_groups(ordering: $ordering_groups) {
                                        id
                                        verbose_name
                                    }
                                    possible_groups{
                                        id
                                        verbose_name
                                    }
                                    free_vm_from_user
                                    vm_action_upon_user_disconnect
                                    vm_disconnect_action_timeout
                                    assigned_connection_types
                                    status
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id,
                    ordering_vms: this.orderingVms.nameSort,
                    ordering_users: this.orderingUsers.nameSort,
                    ordering_groups: this.orderingGroups.nameSort
                }
            });
        }
    }

    // +,-,get вм в стат. пуле

    public addVMStaticPool(pool_id: number, vms: []): Observable<any> {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($pool_id: ID!,$vms: [VmInput!]!) {
                    addVmsToStaticPool(pool_id: $pool_id, vms: $vms) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                pool_id,
                vms
            }
        });
    }

    public prepareVm(data): Observable<any> {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($vm: ID!) {
                     prepareVm(vm_id: $vm) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public removeVMStaticPool(pool_id: number, vm_ids: []) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($pool_id: ID!,$vm_ids: [UUID]!) {
                    removeVmsFromStaticPool(pool_id: $pool_id,vm_ids: $vm_ids) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                pool_id,
                vm_ids
            }
        });
    }

    public removeVmsDynamicPool(pool_id: number, vm_ids: []) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($pool_id: ID!,$vm_ids: [UUID]!) {
                    removeVmsFromDynamicPool(pool_id: $pool_id,vm_ids: $vm_ids) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                pool_id,
                vm_ids
            }
        });
    }

    public getAllVms(controller_id: string, resource_pool_id: string): Observable<any>  {
        return  this.service.watchQuery({
            query: gql` query controllers($controller_id: UUID, $resource_pool_id: UUID) {
                controller(id_: $controller_id) {
                    id
                    vms(resource_pool_id: $resource_pool_id, ordering: "verbose_name") {
                            id
                            verbose_name
                        }
                    }
                }
            `,
            variables: {
                method: 'GET',
                controller_id,
                resource_pool_id,
                get_vms_in_pools: false
            }
        }).valueChanges.pipe(map((data: any) => data.data.controller['vms']));
    }


    // users for pool

    public getAllUsersNoEntitleToPool(pool_id: string): Observable<any>  {
        return  this.service.watchQuery({
            query: gql` query pools($pool_id: ShortString, $entitled: Boolean) {
                pool(pool_id: $pool_id) {
                    users(entitled: $entitled) {
                        username
                        id
                    }
                }
            }
            `,
            variables: {
                method: 'GET',
                entitled: false,
                pool_id
            }
         }).valueChanges.pipe(map(data => data.data['pool']['users']));
    }

    public getAllUsersEntitleToPool(pool_id: string): Observable<any> {
        return this.service.watchQuery({
                query: gql`
                            query  pools($pool_id: ShortString) {
                                pool(pool_id: $pool_id) {
                                    users {
                                        is_superuser
                                        username
                                        id
                                    }
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id,
                entitled: true
            }
        }).valueChanges.pipe(map(data  => data.data['pool']['users']));
    }

    public removeUserEntitlementsFromPool(pool_id: string, users: []) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation pools($pool_id: UUID!,$users: [UUID!]!) {
                                removeUserEntitlementsFromPool(pool_id: $pool_id, users: $users) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id,
                users,
                free_assigned_vms: true
            }
        });
    }

    public entitleUsersToPool(pool_id: string, users: []) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation pools($pool_id: UUID!,$users: [UUID!]!) {
                                entitleUsersToPool(pool_id: $pool_id, users: $users) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id,
                users
            }
        });
    }

    public setVmActions(idPool, poolType, freeVm, action, timeout){
        if (poolType === 'static'){
            return this.service.mutate<any>({
                mutation: gql`
                    mutation pools($idPool: UUID!, $freeVm: Boolean, $timeout: Int, $action: VmActionUponUserDisconnect) {
                        updateStaticPool(pool_id: $idPool, free_vm_from_user: $freeVm, vm_action_upon_user_disconnect: $action, vm_disconnect_action_timeout: $timeout ) {
                            ok
                        }
                    }
                `,
                variables: {
                    method: 'POST',
                    idPool,
                    poolType,
                    freeVm,
                    action,
                    timeout
                }
            });
        }
        if (poolType === 'automated'){
            return this.service.mutate<any>({
                mutation: gql`
                    mutation pools($idPool: UUID!, $freeVm: Boolean, $timeout: Int, $action: VmActionUponUserDisconnect) {
                        updateDynamicPool(pool_id: $idPool, free_vm_from_user: $freeVm, vm_action_upon_user_disconnect: $action, vm_disconnect_action_timeout: $timeout ) {
                            ok
                        }
                    }
                `,
                variables: {
                    method: 'POST',
                    idPool,
                    poolType,
                    freeVm,
                    action,
                    timeout
                }
            });
        }
    }
    public updatePool({pool_id, pool_type }, {connection_types, verbose_name, increase_step, reserve_size, total_size,
                                              vm_disconnect_action_timeout, vm_name_template, create_thin_clones,
                                              enable_vms_remote_access, start_vms, set_vms_hostnames, include_vms_in_ad,
                                              keep_vms_on, ad_ou}) {
        if (pool_type === 'static') {
            return this.service.mutate<any>({
                mutation: gql`
                                mutation pools($connection_types: [PoolConnectionTypes!], $pool_id: UUID!,$verbose_name: ShortString
                                     $keep_vms_on: Boolean ) {
                                    updateStaticPool(connection_types: $connection_types, pool_id: $pool_id, verbose_name: $verbose_name,
                                     keep_vms_on: $keep_vms_on ) {
                                        ok
                                    }
                                }
                `,
                variables: {
                    method: 'POST',
                    pool_id,
                    verbose_name,
                    keep_vms_on,
                    connection_types
                }
            });
        }

        if (pool_type === 'rds') {
            return this.service.mutate<any>({
                mutation: gql`
                                mutation pools($connection_types: [PoolConnectionTypes!], $pool_id: UUID!,$verbose_name: ShortString
                                     $keep_vms_on: Boolean) {
                                    updateRdsPool(connection_types: $connection_types, pool_id: $pool_id, verbose_name: $verbose_name,
                                     keep_vms_on: $keep_vms_on ) {
                                        ok
                                    }
                                }
                `,
                variables: {
                    method: 'POST',
                    pool_id,
                    verbose_name,
                    keep_vms_on,
                    connection_types
                }
            });
        }

        if (pool_type === 'automated' || pool_type === 'guest') {
            return this.service.mutate<any>({
                mutation: gql`
                                mutation pools($connection_types: [PoolConnectionTypes!], $pool_id: UUID!,$verbose_name: ShortString,
                                    $increase_step: Int, $reserve_size: Int, $total_size: Int, $vm_name_template: ShortString,
                                     $keep_vms_on: Boolean, $create_thin_clones: Boolean, $enable_vms_remote_access: Boolean,
                                     $start_vms: Boolean, $set_vms_hostnames: Boolean, $include_vms_in_ad: Boolean, $ad_ou: ShortString, $vm_disconnect_action_timeout: Int ) {
                                    updateDynamicPool(connection_types: $connection_types, pool_id: $pool_id, verbose_name: $verbose_name,
                                        increase_step: $increase_step, reserve_size: $reserve_size, total_size: $total_size,
                                        vm_name_template: $vm_name_template, keep_vms_on: $keep_vms_on,
                                        create_thin_clones: $create_thin_clones, enable_vms_remote_access: $enable_vms_remote_access,
                                        start_vms: $start_vms, set_vms_hostnames: $set_vms_hostnames, include_vms_in_ad: $include_vms_in_ad,
                                        ad_ou: $ad_ou, vm_disconnect_action_timeout: $vm_disconnect_action_timeout ) {
                                        ok
                                    }
                                }
                `,
                variables: {
                    method: 'POST',
                    pool_id,
                    verbose_name,
                    increase_step,
                    reserve_size,
                    total_size,
                    vm_disconnect_action_timeout,
                    vm_name_template,
                    keep_vms_on,
                    create_thin_clones,
                    enable_vms_remote_access,
                    start_vms,
                    set_vms_hostnames,
                    include_vms_in_ad,
                    ad_ou,
                    connection_types
                }
            });
        }
    }

    // назначение пользователя вм

    public assignVmToUser(vm_id: string, users: [string]) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($vm_id: ID!,$users: [UUID!]) {
                    assignVmToUser(vm_id: $vm_id, users: $users) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                vm_id,
                users
            }
        });
    }

    // отлучить пользователя вм

    public freeVmFromUser(vm_id: string, users: [string]) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($vm_id: ID!,$users: [UUID!]) {
                    freeVmFromUser(vm_id: $vm_id, users: $users) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                vm_id,
                users
            }
        });
    }

    //

    public addGrop(id, groups) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $groups: [UUID!]!,
                    $id: UUID!){
                    addPoolGroup(
                        groups: $groups,
                        pool_id: $id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                groups,
                id
            }
        });
    }

    public removeGroup(id, groups) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $groups: [UUID!]!,
                    $id: UUID!){
                    removePoolGroup(
                        groups: $groups,
                        pool_id: $id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                groups,
                id
            }
        });
    }

    public entitleUsersPools(id, users) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $users: [UUID!]!,
                    $id: UUID!){
                    entitleUsersToPool(
                        users: $users,
                        pool_id: $id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                users,
                id
            }
        });
    }

    public removeUserEntitlementsPool(id, users) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $users: [UUID!]!,
                    $id: UUID!){
                    removeUserEntitlementsPool(
                        users: $users,
                        pool_id: $id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                users,
                id
            }
        });
    }

    public backupVms(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $pool_id: UUID!){
                    backupVms(pool_id: $pool_id){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public expandPool(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $pool_id: UUID!){
                    expandPool(pool_id: $pool_id){
                        ok
                        task_id
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public startVm(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                ){
                    startVm(
                        vm_id: $vm_id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public suspendVm(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                ){
                    suspendVm(
                        vm_id: $vm_id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public shutdownVm(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $vm_id: UUID!,
                    $force: Boolean
                ){
                    shutdownVm(
                        force: $force,
                        vm_id: $vm_id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public rebootVm(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $vm_id: UUID!,
                    $force: Boolean
                ){
                    rebootVm(
                        force: $force,
                        vm_id: $vm_id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public backupVm(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                ){
                    backupVm(
                        vm_id: $vm_id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public restoreBackupVm(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                    $file_id: UUID!
                    $node_id: UUID!
                    $datapool_id: UUID
                ){
                    restoreBackupVm(
                        vm_id: $vm_id
                        file_id: $file_id
                        node_id: $node_id
                        datapool_id: $datapool_id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public testDomainVm(vm_id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                ){
                    testDomainVm(vm_id: $vm_id) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                vm_id
            }
        });
    }

    public attachVeilUtils(data) {
        return this.service.mutate<any>({
            mutation: gql` mutation pools($id: UUID!, $controller_id: UUID!) {
                            attachVeilUtilsVm(vm_id: $id, controller_id: $controller_id) {
                                ok
                            }
                        }
                    `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public changeTemplate(data) {
        return this.service.mutate<any>({
            mutation: gql` mutation pools($id: UUID!, $controller_id: UUID!) {
                            changeTemplate(vm_id: $id, controller_id: $controller_id) {
                                ok
                            }
                        }
                    `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public getVm(pool_id: string, vm_id: string, controller_address: string, offset = 0): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query pools($pool_id: ShortString, $vm_id: UUID, $controller_address: UUID, $offset: Int) {
                                pool(pool_id: $pool_id) {
                                    vm(vm_id: $vm_id, controller_id: $controller_address) {
                                        id
                                        verbose_name
                                        description
                                        os_type
                                        os_version
                                        cpu_count
                                        memory_count
                                        tablet
                                        ha_enabled
                                        disastery_enabled
                                        guest_agent
                                        remote_access
                                        spice_stream
                                        user_power_state
                                        boot_type
                                        thin
                                        start_on_boot
                                        address
                                        status
                                        hostname
                                        domain_tags {
                                            colour
                                            verbose_name
                                        }
                                        parent_name
                                        resource_pool {
                                            id
                                            verbose_name
                                        }
                                        controller {
                                            id
                                            verbose_name
                                        }
                                        node {
                                                id
                                                verbose_name
                                        }
                                        assigned_users {
                                                id
                                                username
                                            }
                                        events(offset: $offset) {
                                            id
                                            event_type
                                            message
                                            description
                                            created
                                            user
                                            read_by {
                                                id
                                                username
                                            }
                                        }
                                        spice_connection {
                                            password
                                            host
                                            token
                                            connection_url
                                            connection_type
                                        }
                                        vnc_connection {
                                            password
                                            host
                                            token
                                            connection_url
                                            connection_type
                                        }
                                        count
                                        controller {
                                            id
                                        }
                                        backups {
                                            file_id
                                            vm_id
                                            filename
                                            datapool {
                                                id
                                                verbose_name
                                            }
                                            node {
                                                id
                                                verbose_name
                                            }
                                            assignment_type
                                            size
                                            status
                                        }
                                    }
                                }
                        }
                    `,
            variables: {
                method: 'GET',
                pool_id,
                vm_id,
                controller_address,
                offset
            }
        });
    }

    public getSpice(pool_id: string, vm_id: string, controller_address: string): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql`
                query pools($pool_id: ShortString, $vm_id: UUID, $controller_address: UUID) {
                    pool(pool_id: $pool_id) {
                        vm(vm_id: $vm_id, controller_id: $controller_address) {
                            id
                            spice_connection {
                                password
                                host
                                token
                                connection_url
                                connection_type
                            }
                        }
                    }
                }
            `,
            variables: {
                method: 'GET',
                pool_id,
                vm_id,
                controller_address
            }
        });
    }

    public getVnc(pool_id: string, vm_id: string, controller_address: string): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql`
                query pools($pool_id: ShortString, $vm_id: UUID, $controller_address: UUID) {
                    pool(pool_id: $pool_id) {
                        vm(vm_id: $vm_id, controller_id: $controller_address) {
                            id
                            vnc_connection {
                                password
                                host
                                token
                                connection_url
                                connection_type
                            }
                        }
                    }
                }
            `,
            variables: {
                method: 'GET',
                pool_id,
                vm_id,
                controller_address
            }
        });
    }


  public reserveVm(params: any) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation pools($vm_id: UUID!, $reserve: Boolean!) {
            reserveVm(vm_id: $vm_id, reserve: $reserve){
            ok
          }
        }
      `,
      variables: {
        method: 'POST',
        ...params
      }
    });
  }

  public copyPool(pool_id: string) {
    return this.service.mutate<any>({
        mutation: gql`
            mutation pools($pool_id: UUID!) {
                copyDynamicPool(pool_id: $pool_id) {
                    pool_settings
                }
            }
        `,
        variables: {
            method: 'POST',
            pool_id
        }
        })
    }
}
