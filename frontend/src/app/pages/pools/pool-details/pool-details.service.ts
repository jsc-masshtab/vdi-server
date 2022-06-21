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
    };deleting_computers_from_ad_enabled

    public removePoolAdDeleting(pool_id: number,  deleting_computers_from_ad_enabled: boolean) {
        return this.service.mutate<any>({
            mutation: gql`
                        mutation pools($pool_id: UUID, $deleting_computers_from_ad_enabled: Boolean, $full: Boolean) {
                            removePool(pool_id: $pool_id, deleting_computers_from_ad_enabled: $deleting_computers_from_ad_enabled, full: $full) {
                                ok
                            }
                        }
            `,
            variables: {
                method: 'POST',
                pool_id,
                full: true,
                deleting_computers_from_ad_enabled
            }
        });
    }

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

    public getPool(pool_id: string | number): QueryRef<any, any> {

        return this.service.watchQuery({
            query: gql` query 
                pools(
                    $pool_id: ShortString, 
                    $ordering_vms: ShortString, 
                    $ordering_users: ShortString, 
                    $ordering_groups: ShortString
                ){
                    pool(
                        pool_id: $pool_id
                    ){
                        vms(
                            ordering: $ordering_vms
                        ){
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


                        assigned_groups(ordering: $ordering_groups) {
                            id
                            verbose_name
                        }

                        possible_groups{
                            id
                            verbose_name
                        }

                        pool_id
                        verbose_name
                        pool_type
                        resource_pool_id

                        initial_size
                        reserve_size
                        total_size
                        increase_step
                        vm_disconnect_action_timeout
                        vm_name_template
                        ad_ou

                        create_thin_clones
                        enable_vms_remote_access
                        start_vms
                        set_vms_hostnames
                        include_vms_in_ad
                        keep_vms_on
                        free_vm_from_user

                        assigned_connection_types
                        
                        vm_action_upon_user_disconnect

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

    public addVmsToRdsPool(pool_id: number, vms: []): Observable<any> {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($pool_id: ID!,$vms: [VmInput!]!) {
                    addVmsToRdsPool(pool_id: $pool_id, vms: $vms) {
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

    public removeVmsDynamicPool(pool_id: number, vm_ids: [], _deleting_computers_from_ad_enabled: boolean = false) {
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

    public removeVmsPoolAdDeleting(pool_id: number, vm_ids: [], deleting_computers_from_ad_enabled: boolean) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($pool_id: ID!,$vm_ids: [UUID]!, $deleting_computers_from_ad_enabled: Boolean) {
                    removeVmsFromDynamicPool(pool_id: $pool_id,vm_ids: $vm_ids, deleting_computers_from_ad_enabled: $deleting_computers_from_ad_enabled) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                pool_id,
                vm_ids,
                deleting_computers_from_ad_enabled
            }
        });
    }

    public removeVmsFromRdsPool(pool_id: number, vm_ids: []) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools($pool_id: ID!,$vm_ids: [UUID]!) {
                    removeVmsFromRdsPool(pool_id: $pool_id,vm_ids: $vm_ids) {
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
