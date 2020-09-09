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

    public getPool(pool_id: string | number, type: string): QueryRef<any, any> {
        if (type === 'automated') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: String) {
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
                                        status
                                    }
                                    controller {
                                        id
                                        address
                                    }
                                    initial_size
                                    reserve_size
                                    total_size
                                    increase_step
                                    vm_name_template
                                    users {
                                        username
                                    }
                                    cluster {
                                        verbose_name
                                    }
                                    node {
                                        verbose_name
                                    }
                                    datapool {
                                        verbose_name
                                    }
                                    template {
                                        verbose_name
                                    }
                                    create_thin_clones
                                    keep_vms_on
                                    assigned_roles
                                    possible_roles
                                    assigned_groups {
                                        id
                                        verbose_name
                                    }
                                    possible_groups{
                                        id
                                        verbose_name
                                    }
                                    assigned_connection_types
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id
                }
            });
        }

        if (type === 'static') {
            return this.service.watchQuery({
                query: gql`  query pools($pool_id: String) {
                                pool(pool_id: $pool_id) {
                                    verbose_name
                                    pool_type
                                    vms {
                                        verbose_name
                                        id
                                        user {
                                            username
                                        }
                                        status
                                    }
                                    controller {
                                        id
                                        address
                                    }
                                    cluster_id
                                    node_id
                                    users {
                                        username
                                    }
                                    cluster {
                                        verbose_name
                                    }
                                    node {
                                        verbose_name
                                    }
                                    datapool {
                                        verbose_name
                                    }
                                    assigned_roles
                                    possible_roles
                                    assigned_groups {
                                        id
                                        verbose_name
                                    }
                                    possible_groups{
                                        id
                                        verbose_name
                                    }
                                    assigned_connection_types
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id
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

    public getAllVms(controller_id: string, cluster_id: string, node_id: string): Observable<any>  {
        return  this.service.watchQuery({
            query: gql` query controllers($controller_id: UUID, $cluster_id: UUID, $node_id: UUID) {
                controller(id_: $controller_id) {
                    id
                    vms(cluster_id: $cluster_id,node_id: $node_id) {
                            id
                            verbose_name
                        }
                    }
                }
            `,
            variables: {
                method: 'GET',
                controller_id,
                cluster_id,
                node_id,
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

    public updatePool({pool_id, pool_type }, {connection_types, verbose_name, reserve_size, total_size, vm_name_template, create_thin_clones, keep_vms_on}) {
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
                                    $reserve_size: Int , $total_size: Int , $vm_name_template: String ,
                                     $keep_vms_on: Boolean, $create_thin_clones: Boolean ) {
                                    updateDynamicPool(connection_types: $connection_types, pool_id: $pool_id, verbose_name: $verbose_name,
                                        reserve_size: $reserve_size, total_size: $total_size,
                                        vm_name_template: $vm_name_template, keep_vms_on: $keep_vms_on,
                                         create_thin_clones: $create_thin_clones ) {
                                        ok
                                    }
                                }
                `,
                variables: {
                    method: 'POST',
                    pool_id,
                    verbose_name,
                    reserve_size,
                    total_size,
                    vm_name_template,
                    keep_vms_on,
                    create_thin_clones,
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

    public addRole(id, roles) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $roles: [Role!]!,
                    $id: UUID!){
                    addPoolRole(
                        roles: $roles,
                        pool_id: $id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                roles,
                id
            }
        });
    }

    public removeRole(id, roles) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation pools(
                    $roles: [Role!]!,
                    $id: UUID!){
                    removePoolRole(
                        roles: $roles,
                        pool_id: $id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                roles,
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
                    removePoolRole(
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
}
