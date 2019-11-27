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

    // public getPool({pool_id}, { type }): Observable<any>; // in form-edit
    public getPool(pool_id: string | number , type: string): Observable<any> {
        console.log(pool_id, type);
    
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
                                    datapool {
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

    public addVMStaticPool(pool_id: number, vm_ids: []) { // +
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

    public removeVMStaticPool(pool_id: number, vm_ids: []) { // +
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

    public assignVmToUser(vmId: string, usernameVM: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation AssignVmToUser($vm_id: ID!,$username: String!) {
                                assignVmToUser(vm_id: $vm_id,username: $username) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                vm_id: vmId,
                username: usernameVM
            }
        });
    }

    public freeVmFromUser(vmId: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation FreeVmFromUser($vm_id: ID!) {
                                freeVmFromUser(vm_id: $vm_id) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                vm_id: vmId
            }
        });
    }

    public getAllUsersNoEntitleToPool(pool_id: number): QueryRef<any, any> {  // -
        return  this.service.watchQuery({
             query:  gql` query pools($pool_id: String, $entitled: Boolean) {
                            pool(pool_id: $pool_id) {
                                users(entitled: $entitled) {
                                    username
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

    public removeUserEntitlementsFromPool(poolId: number, entitledUsers: []) { // -
        return this.service.mutate<any>({
            mutation: gql`
                            mutation RemoveUserEntitlementsFromPool($pool_id: ID,$entitled_users: [ID]) {
                                removeUserEntitlementsFromPool(pool_id: $pool_id, entitled_users: $entitled_users) {
                                    freed {
                                        name
                                    }
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: poolId,
                entitled_users: entitledUsers,
                free_assigned_vms: true
            }
        });
    }

    public entitleUsersToPool(poolId: number, entitledUsers: []) { // -
        return this.service.mutate<any>({
            mutation: gql`
                            mutation EntitleUsersToPool($pool_id: ID,$entitled_users: [ID]) {
                                entitleUsersToPool(pool_id: $pool_id, entitled_users: $entitled_users) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: poolId,
                entitled_users: entitledUsers
            }
        });
    }

    public assesUsersToPool(idPool: number): QueryRef<any, any> {
        return this.service.watchQuery({
                query: gql`
                            query  AssesUsersToPool($id: Int) {
                                pool(id: $id) {
                                    users {
                                        username
                                    }
                                }
                            }
            `,
            variables: {
                method: 'POST',
                id: idPool
            }
        });
    }

    public getAllVms(cluster_id: string, node_id: string): QueryRef<any, any> { // +
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


    public updateDynamicPool({pool_id}, {verbose_name, reserve_size, total_size, vm_name_template}) {
        console.log({pool_id}, {verbose_name, reserve_size, total_size, vm_name_template});
        return this.service.mutate<any>({
            mutation: gql`
                            mutation pools($pool_id: UUID!,$verbose_name: String!,
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
                keep_vms_on: true
            }
        });
    }
}

// pool_id?: string, verbose_name?: string, reserve_size?: number,
//                              total_size?: number, vm_name_template?: string
