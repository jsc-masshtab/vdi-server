import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';


@Injectable()
export class PoolDetailsService {

    constructor(private service: Apollo) { }

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

    public getPool(pool_id: string | number, type: string, offset = 0): QueryRef<any, any> {
        if (type === 'automated') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: String, $offset: Int) {
                                pool(pool_id: $pool_id) {
                                    pool_id
                                    verbose_name
                                    pool_type
                                    vms {
                                        id
                                        verbose_name
                                        user {
                                            username
                                        }
                                        user_power_state
                                        qemu_state
                                        status
                                        parent_name
                                        count
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
                                        backups {
                                            filename
                                            datapool {
                                                id
                                                verbose_name
                                            }
                                            assignment_type
                                            size
                                            status
                                        }
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
                                    vm_name_template
                                    ad_cn_pattern
                                    users {
                                        username
                                    }
                                    resource_pool {
                                        verbose_name
                                    }
                                    template {
                                        verbose_name
                                    }
                                    create_thin_clones
                                    prepare_vms
                                    keep_vms_on
                                    assigned_groups {
                                        id
                                        verbose_name
                                    }
                                    possible_groups{
                                        id
                                        verbose_name
                                    }
                                    assigned_connection_types
                                    status
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id,
                    offset
                }
            });
        }

        if (type === 'static') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: String, $offset: Int) {
                                pool(pool_id: $pool_id) {
                                    verbose_name
                                    pool_type
                                    vms {
                                        verbose_name
                                        id
                                        user {
                                            username
                                        }
                                        user_power_state
                                        qemu_state
                                        status
                                        parent_name
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
                                        backups {
                                            filename
                                            datapool {
                                                id
                                                verbose_name
                                            }
                                            assignment_type
                                            size
                                            status
                                        }
                                    }
                                    controller {
                                        id
                                        address
                                        verbose_name
                                    }
                                    resource_pool_id
                                    users {
                                        username
                                    }
                                    resource_pool {
                                        verbose_name
                                    }
                                    assigned_groups {
                                        id
                                        verbose_name
                                    }
                                    possible_groups{
                                        id
                                        verbose_name
                                    }
                                    assigned_connection_types
                                    status
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id,
                    offset
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
                    vms(resource_pool_id: $resource_pool_id) {
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
            query: gql` query pools($pool_id: String, $entitled: Boolean) {
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
                            query  pools($pool_id: String) {
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

    public updatePool({pool_id, pool_type }, {connection_types, verbose_name, increase_step, reserve_size, total_size, vm_name_template, create_thin_clones, prepare_vms, keep_vms_on, ad_cn_pattern}) {
        if (pool_type === 'static') {
            return this.service.mutate<any>({
                mutation: gql`
                                mutation pools($connection_types: [PoolConnectionTypes!], $pool_id: UUID!,$verbose_name: String
                                     $keep_vms_on: Boolean) {
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

        if (pool_type === 'automated') {
            return this.service.mutate<any>({
                mutation: gql`
                                mutation pools($connection_types: [PoolConnectionTypes!], $pool_id: UUID!,$verbose_name: String,
                                    $increase_step: Int , $reserve_size: Int, $total_size: Int , $vm_name_template: String ,
                                     $keep_vms_on: Boolean, $create_thin_clones: Boolean, $prepare_vms: Boolean, $ad_cn_pattern: String ) {
                                    updateDynamicPool(connection_types: $connection_types, pool_id: $pool_id, verbose_name: $verbose_name,
                                        increase_step: $increase_step, reserve_size: $reserve_size, total_size: $total_size,
                                        vm_name_template: $vm_name_template, keep_vms_on: $keep_vms_on,
                                         create_thin_clones: $create_thin_clones, prepare_vms: $prepare_vms, ad_cn_pattern: $ad_cn_pattern ) {
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
                    vm_name_template,
                    keep_vms_on,
                    create_thin_clones,
                    prepare_vms,
                    ad_cn_pattern,
                    connection_types
                }
            });
        }
    }

    // назначение пользователя вм

    public assignVmToUser(vm_id: string, username: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation pools($vm_id: ID!,$username: String!) {
                                assignVmToUser(vm_id: $vm_id,username: $username) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                vm_id,
                username
            }
        });
    }

    // отлучить пользователя вм

    public freeVmFromUser(vm_id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation pools($vm_id: ID!) {
                                freeVmFromUser(vm_id: $vm_id) {
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
}
