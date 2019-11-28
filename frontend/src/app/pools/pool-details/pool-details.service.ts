import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';


@Injectable()
export class PoolDetailsService {

    constructor(private service: Apollo) { }

    public removePool(pool_id: number) {
        return this.service.mutate<any>({
            mutation: gql`
                        mutation pools($pool_id: UUID) {
                            removePool(pool_id: $pool_id) {
                                ok
                            }
                        }
            `,
            variables: {
                method: 'POST',
                pool_id
            }
        });
    }

    public getPool(pool_id: string | number , type: string): Observable<any> {
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
                                        template {
                                            verbose_name
                                        }
                                        user {
                                            username
                                        }
                                        status
                                        state
                                    }
                                    controller {
                                        address
                                    }
                                    initial_size
                                    reserve_size
                                    total_size
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
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
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
                                        state
                                    }
                                    controller {
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
                                }
                            }`,
                variables: {
                    method: 'GET',
                    pool_id
                }
            }).valueChanges.pipe(map(data => data.data['pool']));
        }
    }

    // +,-,get вм в стат. пуле

    public addVMStaticPool(pool_id: number, vm_ids: []) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation pools($pool_id: ID!,$vm_ids: [UUID]!) {
                                addVmsToStaticPool(pool_id: $pool_id, vm_ids: $vm_ids) {
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

    public removeVMStaticPool(pool_id: number, vm_ids: []) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation RemoveVms($pool_id: Int!,$vm_ids: [ID]!) {
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

    public getAllVms(cluster_id: string, node_id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query vms($cluster_id: String,$node_id:String) {
                                    vms(cluster_id: $cluster_id,node_id: $node_id) {
                                        id
                                        verbose_name
                                    }
                                }
                    `,
            variables: {
                method: 'GET',
                cluster_id,
                node_id,
                get_vms_in_pools: false
            }
        });
    }


    // users for pool

    public getAllUsersNoEntitleToPool(pool_id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
             query:  gql` query pools($pool_id: String, $entitled: Boolean) {
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
         });
    }

    public getAllUsersEntitleToPool(pool_id: string): QueryRef<any, any> {
        return this.service.watchQuery({
                query: gql`
                            query  pools($pool_id: String) {
                                pool(pool_id: $pool_id) {
                                    users {
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
        });
    }

    public removeUserEntitlementsFromPool(pool_id: string, users: []) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation pools($pool_id: ID,$users: [ID]) {
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
                            mutation pools($pool_id: ID,$users: [ID]) {
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

    public updatePool({pool_id, pool_type }, {verbose_name, reserve_size, total_size, vm_name_template}) {
        if (pool_type === 'static') {
            return this.service.mutate<any>({
                mutation: gql`
                                mutation pools($pool_id: UUID!,$verbose_name: String
                                     $keep_vms_on: Boolean ) {
                                    updateStaticPool(pool_id: $pool_id, verbose_name: $verbose_name,
                                     keep_vms_on: $keep_vms_on ) {
                                        ok
                                    }
                                }
                `,
                variables: {
                    method: 'POST',
                    pool_id,
                    verbose_name,
                    keep_vms_on: false // сделать у вм
                }
            });
        }

        if (pool_type === 'automated') {
            return this.service.mutate<any>({
                mutation: gql`
                                mutation pools($pool_id: UUID!,$verbose_name: String,
                                    $reserve_size: Int , $total_size: Int , $vm_name_template: String ,
                                     $keep_vms_on: Boolean ) {
                                    updateDynamicPool(pool_id: $pool_id, verbose_name: $verbose_name,
                                        reserve_size: $reserve_size, total_size: $total_size,
                                        vm_name_template: $vm_name_template, keep_vms_on: $keep_vms_on ) {
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
                    keep_vms_on: false
                }
            });
        }
    }

    // назначение пользователя вм

    public assignVmToUser(vm_id: string, username: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation vms($vm_id: ID!,$username: String!) {
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
                            mutation vms($vm_id: ID!) {
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
}
